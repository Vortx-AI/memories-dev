import logging
import numpy as np
import cupy as cp
import torch
import torch.nn as nn
from torch.cuda.amp import autocast
import segmentation_models_pytorch as smp
from diffusers import (
    StableDiffusionImg2ImgPipeline,
    StableDiffusionControlNetPipeline,
    ControlNetModel
)
from PIL import Image
import cv2
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, List
import json
from pathlib import Path
import rasterio
from rasterio.windows import Window
import albumentations as A
from sklearn.preprocessing import MinMaxScaler
import yaml
import warnings
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SyntheticConfig:
    """Configuration for synthetic data generation"""
    # Model paths and settings
    stable_diffusion_model: str = "runwayml/stable-diffusion-v1-5"
    controlnet_model: str = "lllyasviel/control-v11-depth"
    segmentation_model: str = "mit_b5"  # Encoder name for segmentation
    device: str = "cuda"
    fp16: bool = True
    
    # Generation parameters
    batch_size: int = 1
    num_inference_steps: int = 50
    strength: float = 0.75
    guidance_scale: float = 7.5
    
    # Image processing
    image_size: int = 512
    tile_size: int = 256
    overlap: int = 32
    
    # Quality enhancement
    enhance_contrast: bool = True
    denoise: bool = True
    preserve_colors: bool = True
    
    # Data augmentation
    enable_augmentation: bool = True
    aug_brightness_range: Tuple[float, float] = (0.8, 1.2)
    aug_contrast_range: Tuple[float, float] = (0.8, 1.2)
    
    # Output settings
    output_format: str = "png"
    save_intermediates: bool = False
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'SyntheticConfig':
        """Load configuration from YAML file"""
        with open(yaml_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls(**config_dict)

class SyntheticDataGenerator:
    """Advanced synthetic data generator with quality controls and feature preservation"""
    
    def __init__(self, config: SyntheticConfig):
        self.config = config
        self.device = torch.device(config.device)
        self._initialize_models()
        self._setup_augmentation()
        
    def _initialize_models(self):
        """Initialize all required models"""
        logger.info("Initializing models...")
        
        # 1. Stable Diffusion Pipeline
        self.sd_pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
            self.config.stable_diffusion_model,
            torch_dtype=torch.float16 if self.config.fp16 else torch.float32,
            safety_checker=None
        ).to(self.device)
        
        # 2. ControlNet for feature preservation
        controlnet = ControlNetModel.from_pretrained(
            self.config.controlnet_model,
            torch_dtype=torch.float16 if self.config.fp16 else torch.float32
        ).to(self.device)
        
        self.controlnet_pipeline = StableDiffusionControlNetPipeline.from_pretrained(
            self.config.stable_diffusion_model,
            controlnet=controlnet,
            torch_dtype=torch.float16 if self.config.fp16 else torch.float32,
            safety_checker=None
        ).to(self.device)
        
        # 3. Segmentation model for feature extraction
        self.segmentation_model = smp.Unet(
            encoder_name=self.config.segmentation_model,
            encoder_weights="imagenet",
            in_channels=3,
            classes=1,
        ).to(self.device)
        self.segmentation_model.eval()
        
        # Enable memory efficient attention
        self.sd_pipeline.enable_attention_slicing()
        self.controlnet_pipeline.enable_attention_slicing()
        
    def _setup_augmentation(self):
        """Setup augmentation pipeline"""
        if self.config.enable_augmentation:
            self.augmentation = A.Compose([
                A.RandomBrightnessContrast(
                    brightness_limit=self.config.aug_brightness_range,
                    contrast_limit=self.config.aug_contrast_range,
                    p=0.7
                ),
                A.HueSaturationValue(p=0.3),
                A.CLAHE(p=0.5),
                A.Sharpen(p=0.3),
            ])
        else:
            self.augmentation = None
            
    def _extract_features(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """Extract various features from input image"""
        with torch.no_grad():
            # Convert to tensor
            x = torch.from_numpy(image).float().permute(2, 0, 1).unsqueeze(0)
            x = x.to(self.device)
            
            # Get segmentation mask
            seg_mask = self.segmentation_model(x)
            seg_mask = torch.sigmoid(seg_mask)
            
            # Extract edges using Canny
            edges = cv2.Canny(
                (image * 255).astype(np.uint8),
                threshold1=100,
                threshold2=200
            )
            
            # Calculate depth map using traditional computer vision
            gray = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
            depth = cv2.distanceTransform(
                cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1],
                cv2.DIST_L2,
                5
            )
            
            return {
                'segmentation': seg_mask.cpu().numpy(),
                'edges': edges,
                'depth': depth
            }
            
    def _enhance_image(self, image: np.ndarray) -> np.ndarray:
        """Apply various image enhancements"""
        if not self.config.enhance_contrast and not self.config.denoise:
            return image
            
        img_uint8 = (image * 255).astype(np.uint8)
        
        if self.config.denoise:
            img_uint8 = cv2.fastNlMeansDenoisingColored(
                img_uint8,
                None,
                10,
                10,
                7,
                21
            )
            
        if self.config.enhance_contrast:
            lab = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            lab = cv2.merge([l,a,b])
            img_uint8 = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            
        return img_uint8.astype(np.float32) / 255.0
        
    def _preserve_colors(self, synthetic: np.ndarray, reference: np.ndarray) -> np.ndarray:
        """Preserve colors from reference image"""
        if not self.config.preserve_colors:
            return synthetic
            
        # Convert to LAB color space
        synthetic_lab = cv2.cvtColor(
            (synthetic * 255).astype(np.uint8),
            cv2.COLOR_RGB2LAB
        )
        reference_lab = cv2.cvtColor(
            (reference * 255).astype(np.uint8),
            cv2.COLOR_RGB2LAB
        )
        
        # Match color statistics in ab channels
        for i in range(1, 3):  # ab channels
            synthetic_lab[..., i] = (
                (synthetic_lab[..., i] - np.mean(synthetic_lab[..., i])) *
                (np.std(reference_lab[..., i]) / np.std(synthetic_lab[..., i])) +
                np.mean(reference_lab[..., i])
            )
            
        # Convert back to RGB
        return cv2.cvtColor(synthetic_lab, cv2.COLOR_LAB2RGB).astype(np.float32) / 255.0
        
    def generate_synthetic_image(
        self,
        input_image: np.ndarray,
        prompt: str,
        negative_prompt: str = "",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate synthetic image with feature preservation and quality controls
        
        Args:
            input_image: RGB image in range [0, 1]
            prompt: Text prompt for generation
            negative_prompt: Text to discourage in generation
            seed: Random seed for reproducibility
            
        Returns:
            Dictionary containing generated image and metadata
        """
        try:
            if seed is not None:
                torch.manual_seed(seed)
                np.random.seed(seed)
                
            # Extract features
            features = self._extract_features(input_image)
            
            # Prepare control image (depth map)
            control_image = Image.fromarray(features['depth'].astype(np.uint8))
            
            # Enhanced prompts
            enhanced_prompt = f"{prompt}, 8k ultra HD, highly detailed satellite imagery"
            enhanced_negative = f"{negative_prompt}, blurry, low quality, distorted, unrealistic"
            
            # Generate with ControlNet guidance
            with autocast(enabled=self.config.fp16):
                result = self.controlnet_pipeline(
                    prompt=enhanced_prompt,
                    negative_prompt=enhanced_negative,
                    image=control_image,
                    num_inference_steps=self.config.num_inference_steps,
                    guidance_scale=self.config.guidance_scale,
                    controlnet_conditioning_scale=1.0
                ).images[0]
                
            # Convert to numpy
            synthetic = np.array(result).astype(np.float32) / 255.0
            
            # Apply enhancements
            synthetic = self._enhance_image(synthetic)
            
            # Preserve colors if requested
            if self.config.preserve_colors:
                synthetic = self._preserve_colors(synthetic, input_image)
                
            # Apply augmentation if enabled
            if self.augmentation is not None:
                augmented = self.augmentation(image=synthetic)
                synthetic = augmented['image']
                
            # Calculate quality metrics
            metrics = self._calculate_metrics(synthetic, input_image)
            
            return {
                'image': synthetic,
                'metrics': metrics,
                'features': features,
                'seed': seed
            }
            
        except Exception as e:
            logger.error(f"Error in synthetic generation: {str(e)}")
            return None
            
    def _calculate_metrics(self, synthetic: np.ndarray, reference: np.ndarray) -> Dict[str, float]:
        """Calculate image quality metrics"""
        try:
            from skimage.metrics import (
                structural_similarity as ssim,
                peak_signal_noise_ratio as psnr
            )
            
            # Ensure uint8
            if synthetic.dtype != np.uint8:
                synthetic = (synthetic * 255).astype(np.uint8)
            if reference.dtype != np.uint8:
                reference = (reference * 255).astype(np.uint8)
                
            # Calculate metrics
            ssim_value = ssim(reference, synthetic, multichannel=True)
            psnr_value = psnr(reference, synthetic)
            
            # Calculate histogram similarity
            hist_sim = self._calculate_histogram_similarity(reference, synthetic)
            
            return {
                'ssim': float(ssim_value),
                'psnr': float(psnr_value),
                'histogram_similarity': float(hist_sim)
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {}
            
    def _calculate_histogram_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Calculate histogram similarity between images"""
        try:
            similarity = 0
            for i in range(3):  # For each channel
                hist1 = cv2.calcHist([img1], [i], None, [256], [0,256])
                hist2 = cv2.calcHist([img2], [i], None, [256], [0,256])
                similarity += cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            return similarity / 3.0
            
        except Exception as e:
            logger.error(f"Error calculating histogram similarity: {str(e)}")
            return 0.0
            
    def process_large_image(
        self,
        input_path: str,
        output_path: str,
        prompt: str,
        negative_prompt: str = "",
        save_tiles: bool = False
    ) -> None:
        """Process large image by tiling"""
        try:
            # Read image using rasterio for large image support
            with rasterio.open(input_path) as src:
                # Calculate tiles
                width = src.width
                height = src.height
                tile_size = self.config.tile_size
                overlap = self.config.overlap
                
                tiles_x = (width + tile_size - overlap - 1) // (tile_size - overlap)
                tiles_y = (height + tile_size - overlap - 1) // (tile_size - overlap)
                
                # Create output array
                output = np.zeros((height, width, 3), dtype=np.float32)
                weights = np.zeros((height, width), dtype=np.float32)
                
                # Process each tile
                for i in tqdm(range(tiles_y), desc="Processing tiles"):
                    for j in range(tiles_x):
                        # Calculate tile coordinates
                        x = j * (tile_size - overlap)
                        y = i * (tile_size - overlap)
                        
                        # Read tile
                        window = Window(x, y, min(tile_size, width - x), min(tile_size, height - y))
                        tile = src.read(window=window)
                        tile = np.transpose(tile, (1, 2, 0))  # CHW to HWC
                        
                        # Generate synthetic tile
                        result = self.generate_synthetic_image(
                            tile,
                            prompt=prompt,
                            negative_prompt=negative_prompt
                        )
                        
                        if result is None:
                            continue
                            
                        synthetic_tile = result['image']
                        
                        # Create weight mask for blending
                        weight = np.ones_like(synthetic_tile[..., 0])
                        if overlap > 0:
                            # Feather edges
                            weight = cv2.GaussianBlur(weight, (overlap, overlap), overlap/3)
                            
                        # Add to output
                        output[y:y+window.height, x:x+window.width] += synthetic_tile * weight[..., np.newaxis]
                        weights[y:y+window.height, x:x+window.width] += weight
                        
                        # Save individual tile if requested
                        if save_tiles:
                            tile_path = Path(output_path).parent / 'tiles' / f'tile_{i}_{j}.png'
                            tile_path.parent.mkdir(exist_ok=True)
                            Image.fromarray((synthetic_tile * 255).astype(np.uint8)).save(tile_path)
                            
                # Normalize output
                output = np.divide(
                    output,
                    weights[..., np.newaxis],
                    out=np.zeros_like(output),
                    where=weights[..., np.newaxis] > 0
                )
                
                # Save final image
                Image.fromarray((output * 255).astype(np.uint8)).save(output_path)
                
        except Exception as e:
            logger.error(f"Error processing large image: {str(e)}")
            raise

def main():
    """Example usage"""
    # Load configuration
    config = SyntheticConfig.from_yaml('config.yaml')
    
    # Initialize generator
    generator = SyntheticDataGenerator(config)
    
    # Example prompt
    prompt = "A stunning satellite view of agricultural fields with mountains"
    negative_prompt = "clouds, blur, distortion, artifacts"
    
    # Process image
    generator.process_large_image(
        input_path='input.tif',
        output_path='output.png',
        prompt=prompt,
        negative_prompt=negative_prompt,
        save_tiles=True
    )

if __name__ == '__main__':
    main() 