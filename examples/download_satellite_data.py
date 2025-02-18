#!/usr/bin/env python3
"""
Script to download satellite imagery for a small area in San Francisco.
Uses efficient windowed image fetching and scene search.
"""

import os
import sys
import asyncio
import aiohttp
import planetary_computer as pc
import pystac_client
import rasterio
from rasterio.windows import from_bounds
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from shapely.geometry import box
import pyproj
from shapely.ops import transform

# San Francisco Financial District (1km x 1km)
SF_BBOX = {
    'xmin': -122.4018,  # Approximately Market & Montgomery
    'ymin': 37.7914,
    'xmax': -122.3928,  # About 1km east
    'ymax': 37.7994     # About 1km north
}

# Directory structure
EXAMPLES_DIR = Path("examples")
DATA_DIR = EXAMPLES_DIR / "data/satellite"

async def fetch_windowed_band(url, bbox, band_name, data_dir):
    """Fetch only the required window of the image for the given band."""
    output_file = data_dir / f"{band_name}.tif"
    
    # Remove existing file if it exists
    if output_file.exists():
        print(f"Removing existing file: {output_file}")
        output_file.unlink()
    
    print(f"Downloading {band_name}...")
    
    try:
        # Sign URL properly
        signed_asset = pc.sign(url)
        if isinstance(signed_asset, dict) and 'href' in signed_asset:
            signed_url = signed_asset['href']
        else:
            signed_url = signed_asset
            
        if not isinstance(signed_url, str) or not signed_url.startswith('https://'):
            raise ValueError(f"Invalid signed URL for {band_name}")
            
        print(f"Signed URL for {band_name}: {signed_url[:100]}...")
        vsicurl_path = f"/vsicurl/{signed_url}"
        
        # Set up GDAL environment with error handling
        gdal_config = {
            'GDAL_HTTP_MULTIPLEX': 'YES',
            'GDAL_HTTP_VERSION': '2',
            'GDAL_DISABLE_READDIR_ON_OPEN': 'EMPTY_DIR',
            'CPL_VSIL_CURL_ALLOWED_EXTENSIONS': 'tif,tiff',
            'GDAL_MAX_DATASET_POOL_SIZE': '256',
            'CPL_VSIL_CURL_USE_HEAD': 'NO',
            'GDAL_HTTP_RETRY_COUNT': '3',
            'GDAL_HTTP_TIMEOUT': '30',
            'VSI_CACHE': 'TRUE',
            'VSI_CACHE_SIZE': '50000000',
            'GDAL_DISABLE_READDIR_ON_OPEN': 'YES',
            'CPL_DEBUG': 'YES'
        }
        
        with rasterio.Env(**gdal_config):
            try:
                print(f"Opening raster for {band_name}...")
                with rasterio.open(vsicurl_path) as src:
                    print(f"Raster opened successfully for {band_name}")
                    print(f"Raster bounds: {src.bounds}")
                    print(f"Raster size: {src.width}x{src.height}")
                    print(f"Raster CRS: {src.crs}")
                    
                    # Convert input bbox to the raster's CRS if needed
                    if src.crs.to_epsg() != 4326:  # If not WGS84
                        transformer = pyproj.Transformer.from_crs(
                            "epsg:4326",
                            src.crs,
                            always_xy=True
                        )
                        bbox_transformed = transform(
                            transformer.transform,
                            box(bbox['xmin'], bbox['ymin'], bbox['xmax'], bbox['ymax'])
                        )
                        window_bounds = bbox_transformed.bounds
                    else:
                        window_bounds = (
                            bbox['xmin'], bbox['ymin'],
                            bbox['xmax'], bbox['ymax']
                        )
                    
                    # Get the window for our bbox
                    window = from_bounds(*window_bounds, transform=src.transform)
                    
                    # Ensure window is within image bounds
                    window = window.crop(height=src.height, width=src.width)
                    print(f"Window for {band_name}: {window}")
                    
                    if window.width <= 0 or window.height <= 0:
                        raise ValueError(f"Invalid window dimensions for {band_name}")
                    
                    # Calculate output dimensions to target ~5MB file size
                    target_pixels = int(5 * 1024 * 1024 / 2)  # Target 5MB at 2 bytes per pixel
                    current_pixels = window.width * window.height
                    scale_factor = min((target_pixels / current_pixels) ** 0.5, 1.0)
                    
                    out_shape = (
                        max(int(window.height * scale_factor), 100),
                        max(int(window.width * scale_factor), 100)
                    )
                    print(f"Output shape for {band_name}: {out_shape}")
                    
                    # Read the windowed data
                    print(f"Reading {band_name} data...")
                    data = src.read(
                        1,
                        window=window,
                        out_shape=out_shape,
                        resampling=rasterio.enums.Resampling.bilinear
                    )
                    
                    if data is None or data.size == 0:
                        raise ValueError(f"No data read for {band_name}")
                        
                    print(f"Data shape for {band_name}: {data.shape}")
                    print(f"Data statistics - min: {data.min()}, max: {data.max()}, mean: {data.mean()}")
                    
                    # Create output profile
                    profile = src.profile.copy()
                    profile.update({
                        'height': data.shape[0],
                        'width': data.shape[1],
                        'transform': rasterio.windows.transform(window, src.transform),
                        'compress': 'deflate',
                        'predictor': 2,
                        'zlevel': 9,
                        'tiled': True,
                        'blockxsize': 256,
                        'blockysize': 256,
                        'sparse_ok': True,
                        'interleave': 'band'
                    })
                    
                    # Save the windowed data
                    print(f"Saving {band_name} data...")
                    with rasterio.open(output_file, 'w', **profile) as dst:
                        dst.write(data, 1)
                    
                    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
                    print(f"Band {band_name} size: {file_size_mb:.1f} MB")
                    
                    return True
                    
            except rasterio.errors.RasterioIOError as e:
                print(f"IO Error reading {band_name}: {e}")
                return False
                
    except Exception as e:
        print(f"Error downloading {band_name}: {str(e)}")
        if os.path.exists(output_file):
            os.remove(output_file)
        return False

async def download_satellite_data():
    """Download satellite imagery from Planetary Computer."""
    # Create data directory
    data_dir = DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert bbox to geometry
    bbox_list = [SF_BBOX['xmin'], SF_BBOX['ymin'], SF_BBOX['xmax'], SF_BBOX['ymax']]
    aoi = box(*bbox_list)
    
    # Convert to UTM (optional, but useful for reference)
    utm_zone = int((SF_BBOX['xmin'] + 180) / 6) + 1
    epsg_code = f"epsg:326{utm_zone}"
    project = pyproj.Transformer.from_crs("epsg:4326", epsg_code, always_xy=True).transform
    utm_aoi = transform(project, aoi)
    
    print(f"Area of Interest (UTM Zone {utm_zone}):")
    print(f"Bounds: {utm_aoi.bounds}")
    
    # Set up date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
    
    try:
        # Initialize Planetary Computer client
        print("Connecting to Planetary Computer...")
        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=pc.sign_inplace
        )
        
        # Search for scenes
        print("Searching for scenes...")
        search = catalog.search(
            collections=["sentinel-2-l2a"],
            intersects=aoi,
            datetime=time_range,
            query={"eo:cloud_cover": {"lt": 10}},
            sortby=["-datetime"],
            max_items=1
        )
        
        items = list(search.get_items())
        if not items:
            print("No suitable imagery found")
            return
        
        item = items[0]
        print(f"\nFound scene from {item.properties['datetime']}")
        print(f"Cloud cover: {item.properties['eo:cloud_cover']}%")
        print(f"Scene ID: {item.id}")
        
        # Download relevant bands
        bands = {
            "B04": "Red",
            "B08": "NIR",
            "B11": "SWIR"
        }
        
        tasks = []
        for band_id, band_name in bands.items():
            if band_id not in item.assets:
                print(f"Warning: Band {band_id} not found in scene")
                continue
                
            asset = item.assets[band_id]
            print(f"\nProcessing {band_name} band ({band_id})...")
            print(f"Asset href: {asset.href[:100]}...")
            
            task = fetch_windowed_band(asset.href, SF_BBOX, band_id, data_dir)
            tasks.append(task)
        
        if not tasks:
            print("No valid bands to download")
            return
        
        # Wait for all downloads to complete
        results = await asyncio.gather(*tasks)
        
        # Save metadata if all downloads succeeded
        if all(results):
            metadata = {
                "datetime": item.properties["datetime"],
                "cloud_cover": item.properties["eo:cloud_cover"],
                "satellite": item.properties["platform"],
                "scene_id": item.id,
                "bbox": bbox_list,
                "utm_zone": utm_zone,
                "bands_downloaded": list(bands.keys())
            }
            
            metadata_file = data_dir / "metadata.txt"
            with open(metadata_file, 'w') as f:
                for key, value in metadata.items():
                    f.write(f"{key}: {value}\n")
            
            print(f"\nSatellite data downloaded to: {data_dir}")
            print(f"Metadata saved to: {metadata_file}")
        else:
            print("\nSome band downloads failed. Please check the logs.")
            
    except Exception as e:
        print(f"Error during satellite data download: {str(e)}")

def main():
    """Main function to download satellite data."""
    print("=== Downloading Satellite Imagery ===")
    asyncio.run(download_satellite_data())
    print("\n🎉 Download complete!")

if __name__ == "__main__":
    main() 