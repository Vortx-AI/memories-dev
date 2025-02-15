import logging
import numpy as np
import cupy as cp
import rasterio
import torch
import torch.nn.functional as F
from memories_dev.models.segment_anything.modeling.sam import Sam as segmentation_model

def calculate_ndvi(image: np.ndarray) -> np.ndarray:
    """
    Classic NDVI = (NIR - RED) / (NIR + RED + 1e-5)
    Returns single-channel NDVI data in range [0..255] as uint8 by default.
    """
    red_band = image[..., 0]
    nir_band = image[..., 1]
    red_cp = cp.asarray(red_band, dtype=cp.float32)
    nir_cp = cp.asarray(nir_band, dtype=cp.float32)

    ndvi = (nir_cp - red_cp) / (nir_cp + red_cp + 1e-5)
    ndvi = cp.clip(ndvi, -1, 1)
    ndvi = cp.nan_to_num(ndvi, nan=0.0, posinf=1.0, neginf=-1.0)

    # Scale to [0..255]
    ndvi_min = -1.0
    ndvi_max = 1.0
    ndvi_norm = (ndvi - ndvi_min) / (ndvi_max - ndvi_min)
    ndvi_255 = (ndvi_norm * 255).astype(cp.uint8)
    return cp.asnumpy(ndvi_255)  # (H, W)

def transformer_process(image_cp):
    """
    Process the image using the transformer-based segmentation model.
    """
    #try:
        # Convert CuPy array to torch tensor on GPU
    image_tensor = torch.as_tensor(cp.asnumpy(image_cp), device='cuda').float()  # Shape: (H, W, 3)
        # Permute to match torch's expected input shape: (B, C, H, W)
    image_tensor = image_tensor.permute(2, 0, 1).unsqueeze(0)  # Shape: (1, 3, H, W)

        # Normalize the image
    image_min = image_tensor.min()
    image_max = image_tensor.max()
    image_tensor = (image_tensor - image_min) / (image_max - image_min + 1e-5)

        # Pad the image to make its dimensions divisible by 32
    height, width = image_tensor.shape[2], image_tensor.shape[3]
    pad_height = (32 - height % 32) % 32
    pad_width = (32 - width % 32) % 32
    padding = (0, pad_width, 0, pad_height)  # (left, right, top, bottom)
    image_tensor = F.pad(image_tensor, padding, mode='reflect')

        # Run through the model
    with torch.no_grad():
        output = segmentation_model(image_tensor)

        # Remove padding from the output
    output = output[:, :, :height, :width]

        # Process the output
    output = output.squeeze().cpu().numpy()  # Shape: (H, W)
    return output
    #except Exception as e:
    #    logger.error(f"Error in transformer processing: {e}")

    #    return None
