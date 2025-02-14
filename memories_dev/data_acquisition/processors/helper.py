import logging
import numpy as np
import cupy as cp
import rasterio
from flask import Flask, request, jsonify, send_file, send_from_directory
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from rasterio.crs import CRS
from rasterio.warp import transform_bounds
from PIL import Image
import io
from math import pi, atan, sinh
import torch
import torch.nn.functional as F
from torch.multiprocessing import Pool, set_start_method
import segmentation_models_pytorch as smp
import urllib.parse

from processors.process_vis import unload_blip_model
from syndrella.process_imgen import unload_stable_diffusion_model

import geopandas as gpd
from shapely.geometry import Point
from pyproj import CRS, Transformer
#import folium
#from folium.plugins import LayerControl
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import pandas as pd
import numpy as np
import os
from datetime import datetime
import random


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set start method for multiprocessing to 'spawn' for compatibility
#try:
#set_start_method('spawn')
#except RuntimeError:
 #   pass

# Initialize Flask
#app = Flask(__name__, static_folder='static')

# Function to load the transformer-based model
def load_transformer_model():

    """
    Load a transformer-based segmentation model.
    """
    model = smp.Unet(
        encoder_name='mit_b0',        # 'mit_b0' is a transformer encoder in smp
        encoder_weights=None,         # Use None if pre-trained weights are not available
        in_channels=3,                # Adjusted to 3 channels as required by the encoder
        classes=1,                    # Single output channel
    )
    # Move model to GPU
    model = model.cuda()
    model.eval()
    return model


# Function to fetch and process only the required window of an image
def fetch_windowed_image(b04_url, b08_url, bbox):
    """
    Fetch only the required window of the image for the given bounding box.
    """
    print("inside fetch window")
    print(b04_url)
    print(b08_url)
    #try:
        # Fetch B04 (Red band)
    with rasterio.Env():
        with rasterio.open(b04_url) as src_b04:
            window = from_bounds(*bbox, transform=src_b04.transform)
            red_band = src_b04.read(1, window=window, out_dtype='float32', resampling=Resampling.bilinear)
            if red_band.size == 0:
                logger.error("Red band data is empty for the specified bounding box.")
                return None

            # Fetch B08 (NIR band)
        with rasterio.open(b08_url) as src_b08:
            window = from_bounds(*bbox, transform=src_b08.transform)
            nir_band = src_b08.read(1, window=window, out_dtype='float32', resampling=Resampling.bilinear)
            if nir_band.size == 0:
                logger.error("NIR band data is empty for the specified bounding box.")
                return None

        # Stack the bands to create a 3-channel image by duplicating one band
    image = np.stack([red_band, nir_band, red_band], axis=-1)  # Shape: (H, W, 3)

    return image
    #except Exception as e:
    #    logger.error(f"Failed to fetch image: {e}")
    #    return None


def transformer_process(image_cp):
    """
    Process the image using the transformer-based segmentation model.
    """

    segmentation_model = load_transformer_model()
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

# Function to calculate NDVI using CuPy
def calculate_ndvi(red_band_cp, nir_band_cp):
    """
    Calculate NDVI using CuPy for GPU acceleration.
    """
    ndvi = (nir_band_cp - red_band_cp) / (nir_band_cp + red_band_cp + 1e-5)
    ndvi = cp.clip(ndvi, -1, 1)
    ndvi = cp.nan_to_num(ndvi, nan=0.0, posinf=1.0, neginf=-1.0)
    return ndvi

    """
    Load a transformer-based segmentation model.
    """
    model = smp.Unet(
        encoder_name='mit_b0',        # 'mit_b0' is a transformer encoder in smp
        encoder_weights=None,         # Use None if pre-trained weights are not available
        in_channels=3,                # Adjusted to 3 channels as required by the encoder
        classes=1,                    # Single output channel
    )
    # Move model to GPU
    model = model.cuda()
    model.eval()
    return model


# Function to fetch and process only the required window of an image
def fetch_windowed_image(b04_url, b08_url, bbox):
    """
    Fetch only the required window of the image for the given bounding box.
    """
    print("inside fetch window")
    print(b04_url)
    print(b08_url)
    #try:
        # Fetch B04 (Red band)
    with rasterio.Env():
        with rasterio.open(b04_url) as src_b04:
            window = from_bounds(*bbox, transform=src_b04.transform)
            red_band = src_b04.read(1, window=window, out_dtype='float32', resampling=Resampling.bilinear)
            if red_band.size == 0:
                logger.error("Red band data is empty for the specified bounding box.")
                return None

            # Fetch B08 (NIR band)
            with rasterio.open(b08_url) as src_b08:
                window = from_bounds(*bbox, transform=src_b08.transform)
                nir_band = src_b08.read(1, window=window, out_dtype='float32', resampling=Resampling.bilinear)
                if nir_band.size == 0:
                    logger.error("NIR band data is empty for the specified bounding box.")
                    return None

        # Stack the bands to create a 3-channel image by duplicating one band
    image = np.stack([red_band, nir_band, red_band], axis=-1)  # Shape: (H, W, 3)

    return image
    #except Exception as e:
    #    logger.error(f"Failed to fetch image: {e}")
    #    return None


def transformer_process(image_cp):
    """
    Process the image using the transformer-based segmentation model.
    """

    segmentation_model = load_transformer_model()
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

# Function to calculate NDVI using CuPy
def calculate_ndvi(red_band_cp, nir_band_cp):
    """
    Calculate NDVI using CuPy for GPU acceleration.
    """
    ndvi = (nir_band_cp - red_band_cp) / (nir_band_cp + red_band_cp + 1e-5)
    ndvi = cp.clip(ndvi, -1, 1)
    ndvi = cp.nan_to_num(ndvi, nan=0.0, posinf=1.0, neginf=-1.0)
    return ndvi

# Function to convert tile coordinates to bounding box
def num2deg(xtile, ytile, zoom):
    """
    Converts tile numbers to latitude and longitude in degrees.
    """
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = atan(sinh(pi * (1 - 2 * ytile / n)))
    lat_deg = lat_rad * 180.0 / pi
    return lat_deg, lon_deg

def tile_coords_to_bbox(x, y, z):
    """
    Returns bounding box in WGS84 coordinates for given tile x, y, z.
    Returns [min_lon, min_lat, max_lon, max_lat]
    """
    # Note that tile y origin is at the top, so as y increases, lat decreases
    lat1, lon1 = num2deg(x, y, z)           # NW corner
    lat2, lon2 = num2deg(x + 1, y + 1, z)   # SE corner
    min_lon = lon1
    min_lat = lat2
    max_lon = lon2
    max_lat = lat1
    bbox = [min_lon, min_lat, max_lon, max_lat]
    return bbox

def generate_tile(b04_url, b08_url, bbox, tile_size, algorithm):
    # Load the transformer-based model once at startup
    #unload_blip_model()
    unload_stable_diffusion_model()
    segmentation_model = load_transformer_model()

    # Fetch only the required tile window
    #try:

    image_cp = fetch_windowed_image(b04_url, b08_url, bbox)
    if image_cp is None:
        return None

    if algorithm == 'ndvi':
        red_band_cp = image_cp[..., 0]
        nir_band_cp = image_cp[..., 1]
        processed_data_cp = calculate_ndvi(red_band_cp, nir_band_cp)
    elif algorithm == 'transformer':
        processed_data = transformer_process(image_cp)
        if processed_data is None:
            return None
        processed_data_cp = cp.asarray(processed_data)
    else:
        logger.error(f"Unsupported algorithm: {algorithm}")
        return None


    if algorithm == 'ndvi':
        red_band_cp = image_cp[..., 0]
        nir_band_cp = image_cp[..., 1]
        processed_data_cp = calculate_ndvi(red_band_cp, nir_band_cp)
    elif algorithm == 'transformer':
        processed_data = transformer_process(image_cp)
        if processed_data is None:
            return None
        processed_data_cp = cp.asarray(processed_data)
    else:
        logger.error(f"Unsupported algorithm: {algorithm}")
        return None

    # Ensure processed_data is not empty
    if processed_data_cp is None or processed_data_cp.size == 0:
        logger.error("Processed data is empty after processing.")
        return None

    # Normalize data to 0-255
    data_min = processed_data_cp.min()
    data_max = processed_data_cp.max()
    if data_max - data_min != 0:
        processed_data_cp = (processed_data_cp - data_min) / (data_max - data_min)
    else:
        processed_data_cp = processed_data_cp - data_min  # Should be all zeros
    processed_data_cp = (processed_data_cp * 255).astype(cp.uint8)

    # Bring data back to CPU for saving
    processed_data_np = cp.asnumpy(processed_data_cp)

    image = Image.fromarray(processed_data_np)

        # Resize to tile size
    image = image.resize((tile_size, tile_size), Image.LANCZOS)

        # Save image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr
    #except Exception as e:
     #   logger.error(f"Error generating tile: {e}")
      #  return None

#read STAC files

#kml
# Define the path to the input KML file
def kml_reader(input_kml):

    # Read the KML file using GeoPandas
    geo_data = gpd.read_file(input_kml)
    return geo_data




#Reproject to a Conventional Planar CRS

def reproject(geo_data,utm_zone): #geo_data is of type geo dataframe
    target_crs = CRS.from_epsg(utm_zone)  # Replace with appropriate UTM zone 32630
    geo_data_planar = geo_data.to_crs(target_crs)
    return geo_data_planar


#Encryption

#Generates a time-sensitive AES key based on the current UTC hour.
def get_aes_key():

    # Get current UTC time truncated to the hour
    time_stamp = datetime.utcnow().strftime("%Y-%m-%d-%H")

    # Create SHA256 hash of the timestamp
    sha256 = hashlib.sha256()
    sha256.update(time_stamp.encode('utf-8'))
    key_hex = sha256.hexdigest()
    # Convert hex to bytes and take the first 32 bytes for AES-256
    key_bytes = bytes.fromhex(key_hex)[:32]
    return key_bytes

def aes_encrypt(plaintext, key):
    """
    Encrypts plaintext using AES CBC mode with PKCS7 padding.
    """
    # Initialize cipher with a random IV
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())

    
    # Pad plaintext to block size
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
    
    # Encrypt data
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    

    # Pad plaintext to block size
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()

    # Encrypt data
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return iv + ciphertext  # Prepend IV for decryption

def aes_decrypt(ciphertext, key):
    """
    Decrypts ciphertext using AES CBC mode with PKCS7 padding.
    """
    # Extract IV
    iv = ciphertext[:16]
    actual_ciphertext = ciphertext[16:]
    
    # Initialize cipher
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    
    # Decrypt data
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()
    
    # Unpad plaintext
    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
    

    # Initialize cipher
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())

    # Decrypt data
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()

    # Unpad plaintext
    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

    return plaintext.decode('utf-8')

def encode_coords_fractal_aes(x, y, fractal_name="hilbert"):
    """
    Applies fractal transformation and AES encryption to coordinates.
    Returns encrypted X and Y as numeric placeholders.
    """
    # Apply fractal transformation
    fractal_func = fractal_algos.get(fractal_name)
    if fractal_func is None:
        raise ValueError(f"Fractal algorithm '{fractal_name}' not found.")
    transformed_x, transformed_y = fractal_func(x, y)

    
    # Combine coordinates into plaintext
    plaintext = f"{transformed_x},{transformed_y}"
    
    # Get AES key
    key = get_aes_key()
    
    # Encrypt plaintext
    ciphertext = aes_encrypt(plaintext, key)
    
    # Encode ciphertext to hexadecimal
    cipher_hex = ciphertext.hex()
    
    # Use length of cipher_hex as encrypted X
    enc_x = len(cipher_hex)
    
    # Use sum of ASCII values modulo 100000 as encrypted Y (naive numeric representation)
    enc_y = sum(cipher_hex.encode('utf-8')) % 100000
    


    # Combine coordinates into plaintext
    plaintext = f"{transformed_x},{transformed_y}"

    # Get AES key
    key = get_aes_key()

    # Encrypt plaintext
    ciphertext = aes_encrypt(plaintext, key)

    # Encode ciphertext to hexadecimal
    cipher_hex = ciphertext.hex()

    # Use length of cipher_hex as encrypted X
    enc_x = len(cipher_hex)

    # Use sum of ASCII values modulo 100000 as encrypted Y (naive numeric representation)
    enc_y = sum(cipher_hex.encode('utf-8')) % 100000

    return enc_x, enc_y

def decode_coords_fractal_aes(enc_x, enc_y):
    """
    Placeholder for decoding coordinates. Since encryption is not invertible in this context,
    returns NaN values.
    """
    return np.nan, np.nan

def encode_geodataframe(sf_object, encode_func=encode_coords_fractal_aes, fractal_name="hilbert"):
    """
    Encodes the coordinates of a GeoDataFrame using the specified encoding function.
    """
    encoded_coords = sf_object.geometry.apply(lambda geom: encode_func(geom.x, geom.y, fractal_name))
    sf_object_enc = sf_object.copy()
    sf_object_enc['geometry'] = [Point(xy) for xy in encoded_coords]
    return sf_object_enc

def decode_geodataframe(sf_object, decode_func=decode_coords_fractal_aes):
    """
    Decodes the coordinates of a GeoDataFrame using the specified decoding function.
    """
    decoded_coords = sf_object.geometry.apply(lambda geom: decode_func(geom.x, geom.y))
    sf_object_dec = sf_object.copy()
    sf_object_dec['geometry'] = [Point(xy) for xy in decoded_coords]
    return sf_object_dec



#fractal transformations

def fractal_transform_hilbert(x, y):
    # Placeholder for a Hilbert curve-inspired transformation
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    new_x = r * np.cos(theta + r)
    new_y = r * np.sin(theta + r)
    return new_x, new_y

def fractal_transform_spiral(x, y):
    # Simple spiral transformation
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    new_x = (r + 0.5) * np.cos(theta + 2)
    new_y = (r + 0.5) * np.sin(theta + 2)
    return new_x, new_y

def fractal_transform_koch(x, y):
    # Placeholder Koch-like transformation
    new_x = x + 0.5 * np.sin(y)
    new_y = y + 0.5 * np.sin(x)
    return new_x, new_y

def fractal_transform_sierpinski(x, y):
    # Naive Sierpinski-like transformation
    new_x = 0.5 * x
    new_y = y + 0.3 * x if (x + y) > 0 else y - 0.3 * x
    return new_x, new_y

def fractal_transform_julia(x, y):
    # Placeholder Julia set transformation
    c = complex(0.355, 0.355)
    z = complex(x, y)
    z_new = z**2 + c
    return z_new.real, z_new.imag

def fractal_transform_random(x, y):
    # Randomly apply one of the fractal transformations
    fractal_funcs = [
        fractal_transform_spiral,
        fractal_transform_koch,
        fractal_transform_sierpinski,
        fractal_transform_julia
    ]
    func = random.choice(fractal_funcs)
    return func(x, y)

# Store fractal algorithms in a dictionary
fractal_algos = {
    "hilbert": fractal_transform_hilbert,
    "spiral": fractal_transform_spiral,
    "koch": fractal_transform_koch,
    "sierpinski": fractal_transform_sierpinski,
    "julia": fractal_transform_julia,
    "random": fractal_transform_random

}                      
   

