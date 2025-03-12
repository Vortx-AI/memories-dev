"""
Vortx Synthetic Data Generation Module

This module provides advanced synthetic data generation capabilities for satellite imagery,
including terrain, land cover, urban areas, and atmospheric effects.
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import rasterio
from rasterio.transform import from_bounds
import geopandas as gpd
from shapely.geometry import box, Polygon, MultiPolygon
import noise
from scipy.ndimage import gaussian_filter
from concurrent.futures import ThreadPoolExecutor
import logging
from tqdm import tqdm
import os
import torch
from diffusers import StableDiffusionPipeline
from PIL import Image, ImageDraw, ImageFont
import random
import numpy.typing as npt

#from memories.utils.exceptions import SyntheticDataError
#from memories.utils.validation import validate_parameters

logger = logging.getLogger(__name__)

# Initialize StableDiffusion pipeline
pipe = None

# Type definitions
RasterType = npt.NDArray[np.float32]
BBox = Tuple[float, float, float, float]  # (min_x, min_y, max_x, max_y)

def initialize_stable_diffusion():
    """Initialize the Stable Diffusion pipeline"""
    global pipe
    if pipe is None:
        pipe = StableDiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-2-1",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        ).to("cuda" if torch.cuda.is_available() else "cpu")

@dataclass
class TerrainParams:
    """Parameters for terrain generation"""
    elevation_range: Tuple[float, float] = (-100, 4000)
    roughness: float = 0.5
    persistence: float = 0.5
    lacunarity: float = 2.0
    octaves: int = 6
    seed: Optional[int] = None

@dataclass
class LandCoverParams:
    """Parameters for land cover generation"""
    classes: List[str] = None
    class_weights: Optional[List[float]] = None
    patch_size_range: Tuple[int, int] = (10, 100)
    smoothing: float = 1.0
    random_state: Optional[int] = None

@dataclass
class AtmosphericParams:
    """Parameters for atmospheric effects"""
    cloud_cover: float = 0.3
    cloud_type: str = "cumulus"
    haze: float = 0.2
    aerosol_depth: float = 0.1
    sun_elevation: float = 45.0
    sun_azimuth: float = 180.0

class SyntheticDataGenerator:
    """Advanced synthetic satellite data generator"""
    
    def __init__(
        self,
        output_size: Tuple[int, int] = (1024, 1024),
        resolution: float = 10.0,
        num_bands: int = 4,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        num_workers: int = 4
    ):
        """Initialize the generator
        
        Args:
            output_size: Output image size (height, width)
            resolution: Spatial resolution in meters
            num_bands: Number of spectral bands
            device: Computation device
            num_workers: Number of parallel workers
        """
        self.output_size = output_size
        self.resolution = resolution
        self.num_bands = num_bands
        self.device = torch.device(device)
        self.num_workers = num_workers
        
        # Initialize components
        self._init_models()
        self._init_transforms()
        
    def _init_models(self):
        """Initialize ML models for generation"""
        try:
            self.terrain_model = self._load_terrain_model()
            self.landcover_model = self._load_landcover_model()
            self.atmospheric_model = self._load_atmospheric_model()
        except Exception as e:
            logger.error(f"Error initializing models: {str(e)}")
            #raise SyntheticDataError("Failed to initialize synthetic data models")
            
    def _init_transforms(self):
        """Initialize data transformations"""
        self.transforms = {
            "normalize": self._normalize_data,
            "add_noise": self._add_noise,
            "apply_atmosphere": self._apply_atmospheric_effects
        }
        
    def generate_terrain(
        self,
        bbox: BBox,
        params: Optional[TerrainParams] = None
    ) -> RasterType:
        """Generate synthetic terrain data
        
        Args:
            bbox: Bounding box for generation
            params: Terrain generation parameters
            
        Returns:
            Synthetic terrain raster
        """
        params = params or TerrainParams()
        #validate_parameters(params)
        
        try:
            # Generate base terrain using Perlin noise
            elevation = self._generate_perlin_terrain(
                params.elevation_range,
                params.roughness,
                params.persistence,
                params.lacunarity,
                params.octaves,
                params.seed
            )
            
            # Apply post-processing
            elevation = self._post_process_terrain(elevation)
            
            # Create raster with georeference
            transform = from_bounds(*bbox, *self.output_size)
            terrain = self._create_raster(elevation, transform)
            
            return terrain
            
        except Exception as e:
            logger.error(f"Error generating terrain: {str(e)}")
            #raise SyntheticDataError("Failed to generate synthetic terrain")
            
    def generate_landcover(
        self,
        bbox: BBox,
        params: Optional[LandCoverParams] = None
    ) -> RasterType:
        """Generate synthetic land cover
        
        Args:
            bbox: Bounding box for generation
            params: Land cover generation parameters
            
        Returns:
            Synthetic land cover raster
        """
        params = params or LandCoverParams()
        #validate_parameters(params)
        
        try:
            # Generate base land cover classes
            landcover = self._generate_landcover_classes(
                params.classes,
                params.class_weights,
                params.patch_size_range,
                params.random_state
            )
            
            # Apply smoothing and transitions
            landcover = self._smooth_landcover(landcover, params.smoothing)
            
            # Create raster with georeference
            transform = from_bounds(*bbox, *self.output_size)
            landcover = self._create_raster(landcover, transform)
            
            return landcover
            
        except Exception as e:
            logger.error(f"Error generating land cover: {str(e)}")
            #raise SyntheticDataError("Failed to generate synthetic land cover")
            
    def generate_multispectral(
        self,
        bbox: BBox,
        terrain: Optional[RasterType] = None,
        landcover: Optional[RasterType] = None,
        atmospheric_params: Optional[AtmosphericParams] = None
    ) -> RasterType:
        """Generate synthetic multispectral imagery
        
        Args:
            bbox: Bounding box for generation
            terrain: Optional terrain raster
            landcover: Optional land cover raster
            atmospheric_params: Atmospheric effect parameters
            
        Returns:
            Synthetic multispectral raster
        """
        try:
            # Generate base spectral data
            spectral = self._generate_spectral_data(terrain, landcover)
            
            # Apply atmospheric effects
            if atmospheric_params:
                spectral = self._apply_atmospheric_effects(
                    spectral,
                    atmospheric_params
                )
                
            # Create raster with georeference
            transform = from_bounds(*bbox, *self.output_size)
            multispectral = self._create_raster(spectral, transform)
            
            return multispectral
            
        except Exception as e:
            logger.error(f"Error generating multispectral data: {str(e)}")
            #raise SyntheticDataError("Failed to generate synthetic multispectral data")
            
    def _generate_perlin_terrain(
        self,
        elevation_range: Tuple[float, float],
        roughness: float,
        persistence: float,
        lacunarity: float,
        octaves: int,
        seed: Optional[int] = None
    ) -> np.ndarray:
        """Generate terrain using Perlin noise"""
        if seed is not None:
            np.random.seed(seed)
            
        shape = self.output_size
        scale = 100.0
        
        def _generate_octave(size, frequency):
            world = np.zeros(size)
            for i in range(size[0]):
                for j in range(size[1]):
                    world[i][j] = noise.pnoise2(
                        i/scale * frequency,
                        j/scale * frequency,
                        octaves=1,
                        persistence=persistence,
                        lacunarity=lacunarity,
                        repeatx=size[0],
                        repeaty=size[1],
                        base=seed if seed else 0
                    )
            return world
            
        terrain = np.zeros(shape)
        frequency = 1
        amplitude = 1
        max_value = 0
        
        for _ in range(octaves):
            terrain += _generate_octave(shape, frequency) * amplitude
            max_value += amplitude
            frequency *= 2
            amplitude *= persistence
            
        terrain = (terrain / max_value)
        terrain = (terrain + 1) / 2
        
        # Scale to elevation range
        min_elevation, max_elevation = elevation_range
        terrain = terrain * (max_elevation - min_elevation) + min_elevation
        
        return terrain
        
    def _generate_landcover_classes(
        self,
        classes: List[str],
        weights: Optional[List[float]],
        patch_size_range: Tuple[int, int],
        random_state: Optional[int] = None
    ) -> np.ndarray:
        """Generate land cover classification"""
        if random_state is not None:
            np.random.seed(random_state)
            
        if classes is None:
            classes = ["water", "urban", "forest", "agriculture", "barren"]
            
        if weights is None:
            weights = [0.1, 0.2, 0.3, 0.3, 0.1]
            
        num_classes = len(classes)
        shape = self.output_size
        
        # Initialize empty classification
        landcover = np.zeros(shape, dtype=np.int32)
        
        # Generate random patches
        min_size, max_size = patch_size_range
        remaining = np.ones(shape, dtype=bool)
        
        while np.any(remaining):
            # Select random class
            class_idx = np.random.choice(num_classes, p=weights)
            
            # Generate random patch
            size = np.random.randint(min_size, max_size)
            i = np.random.randint(0, shape[0])
            j = np.random.randint(0, shape[1])
            
            # Create circular patch
            y, x = np.ogrid[-size:size+1, -size:size+1]
            mask = x*x + y*y <= size*size
            
            # Apply patch
            patch_i = slice(max(0, i-size), min(shape[0], i+size+1))
            patch_j = slice(max(0, j-size), min(shape[1], j+size+1))
            mask_i = slice(max(0, -(i-size)), min(mask.shape[0], shape[0]-(i-size)))
            mask_j = slice(max(0, -(j-size)), min(mask.shape[1], shape[1]-(j-size)))
            
            patch_remaining = remaining[patch_i, patch_j]
            patch_mask = mask[mask_i, mask_j]
            
            landcover[patch_i, patch_j][patch_remaining & patch_mask] = class_idx
            remaining[patch_i, patch_j][patch_mask] = False
            
        return landcover
        
    def _apply_atmospheric_effects(
        self,
        data: np.ndarray,
        params: AtmosphericParams
    ) -> np.ndarray:
        """Apply atmospheric effects to imagery"""
        # Add clouds
        if params.cloud_cover > 0:
            clouds = self._generate_clouds(
                params.cloud_cover,
                params.cloud_type
            )
            data = self._blend_clouds(data, clouds)
            
        # Add haze
        if params.haze > 0:
            haze = self._generate_haze(params.haze)
            data = self._blend_haze(data, haze)
            
        # Apply atmospheric scattering
        if params.aerosol_depth > 0:
            data = self._apply_scattering(
                data,
                params.aerosol_depth,
                params.sun_elevation,
                params.sun_azimuth
            )
            
        return data
        
    def _create_raster(
        self,
        data: np.ndarray,
        transform: rasterio.transform.Affine
    ) -> RasterType:
        """Create a georeferenced raster"""
        return {
            "data": data,
            "transform": transform,
            "crs": "EPSG:4326"
        } 
    
    def synthetic_image(self, prompt: str, seed: int = None) -> Image.Image:
        """Generate synthetic image using Stable Diffusion
        
        Args:
            prompt: Text prompt for image generation
            seed: Optional random seed
            
        Returns:
            Generated PIL Image
        """
        global pipe
        if pipe is None:
            initialize_stable_diffusion()
        
        if seed is not None:
            torch.manual_seed(seed)
        
        # Generate image
        image = pipe(prompt).images[0]
        return image

def add_watermark(image: Image.Image, logo_path: str) -> Image.Image:
    """
    Adds a watermark with a logo to the given image.

    Args:
        image (PIL.Image.Image): The original image.
        logo_path (str): Path to the logo image.

    Returns:
        PIL.Image.Image: The image with the watermark.
    """
    try:
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Create a new transparent layer for the watermark
        watermark_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))

        # Add the logo to the bottom-left corner
        if os.path.exists(logo_path):
            logo = Image.open(logo_path).convert("RGBA")
            logo_size = (50, 50)  # Adjust size as needed
            logo.thumbnail(logo_size)  # Removed `Image.ANTIALIAS`

            margin = 10  # Margin from edges
            logo_position = (margin, image.height - logo.height - margin)
            watermark_layer.paste(logo, logo_position, logo)

        # Combine the original image with the watermark layer
        watermarked_image = Image.alpha_composite(image, watermark_layer)
        return watermarked_image.convert("RGB")

    except Exception as e:
        logger.error(f"Error adding watermark: {e}")
        raise RuntimeError("Failed to add watermark to the image.") from e
