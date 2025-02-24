#!/usr/bin/env python3
"""
Example script demonstrating data download using Overture and Sentinel APIs.
"""

import os
import sys
import asyncio
from pathlib import Path
from memories.data_acquisition.sources.overture_api import OvertureAPI
from memories.data_acquisition.sources.sentinel_api import SentinelAPI
from memories import Config

# San Francisco Financial District (1km x 1km)
SF_BBOX = {
    'xmin': -122.4018,  # Approximately Market & Montgomery
    'ymin': 37.7914,
    'xmax': -122.3928,  # About 1km east
    'ymax': 37.7994     # About 1km north
}

def setup_directories(config):
    """Create all necessary data directories."""
    paths = config.config['data_acquisition']['paths']
    for path in paths.values():
        Path(path).mkdir(parents=True, exist_ok=True)

async def main():
    """Download Overture Maps and satellite data for San Francisco."""
    print("=== Downloading Data for San Francisco Financial District ===")
    
    # Initialize config with correct path
    project_root = Path(__file__).parent.parent
    config_path = project_root / "memories" / "config" / "config.yaml"
    config = Config(config_path=str(config_path))
    
    # Create directories
    setup_directories(config)
    
    # Get paths from config
    paths = config.config['data_acquisition']['paths']
    
    # Initialize APIs with config paths
    overture_api = OvertureAPI(data_dir=paths['overture'])
    sentinel_api = SentinelAPI(data_dir=paths['satellite'])
    
    # Download Overture data
    print("\n=== Downloading Overture Maps Data ===")
    overture_results = await overture_api.search(SF_BBOX)
    
    if overture_results and 'features' in overture_results:
        print("\nSuccessfully downloaded Overture data:")
        print(f"- Number of features: {len(overture_results['features'])}")
        
        # Count features by type
        feature_types = {}
        for feature in overture_results['features']:
            feat_type = feature['properties'].get('type', 'unknown')
            feature_types[feat_type] = feature_types.get(feat_type, 0) + 1
        
        print("- Feature types:")
        for feat_type, count in feature_types.items():
            print(f"  • {feat_type}: {count}")
    else:
        print("\nNo Overture data found or download failed")
    
    # Download satellite data
    print("\n=== Downloading Satellite Imagery ===")
    satellite_results = await sentinel_api.search(
        bbox=SF_BBOX,
        cloud_cover=10.0,
        bands={
            "B04": "Red",
            "B08": "NIR",
            "B11": "SWIR"
        }
    )
    
    if satellite_results and 'features' in satellite_results:
        print("\nFound satellite data:")
        for scene in satellite_results['features']:
            print(f"- Scene ID: {scene['id']}")
            print(f"- Date: {scene['properties']['datetime']}")
            print(f"- Cloud cover: {scene['properties'].get('eo:cloud_cover', 'N/A')}%")
            print(f"- Available bands: {', '.join(scene['assets'].keys())}")
    else:
        print("\nNo satellite data found or search failed")
    
    print("\n🎉 Download complete!")

if __name__ == "__main__":
    # Add project root to Python path
    project_root = str(Path(__file__).parent.parent)
    if project_root not in sys.path:
        print(f"Added {project_root} to Python path")
        sys.path.append(project_root)
    
    asyncio.run(main()) 