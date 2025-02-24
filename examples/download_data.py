#!/usr/bin/env python3
"""
Example script demonstrating data download using Overture API with direct S3 access and bbox filtering.
Downloads both Overture Maps data and Sentinel imagery for San Francisco Financial District.
"""

import os
import sys
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
    
    try:
        # Initialize config with correct path
        project_root = Path(__file__).parent.parent
        config_path = project_root / "memories" / "config" / "config.yaml"
        config = Config(config_path=str(config_path))
        
        # Create directories
        setup_directories(config)
        
        # Get paths from config
        paths = config.config['data_acquisition']['paths']
        
        # Initialize APIs
        overture_api = OvertureAPI(data_dir=paths['overture'])
        sentinel_api = SentinelAPI(data_dir=paths['satellite'])
        
        try:
            # Download Overture data
            print("\n=== Downloading Overture Maps Data from S3 ===")
            print("Note: Using DuckDB for direct S3 access and bbox filtering")
            
            # Download the data with bbox filtering
            download_results = overture_api.download_data(SF_BBOX)
            
            if any(download_results.values()):
                print("\nSuccessfully downloaded filtered Overture data:")
                for theme, success in download_results.items():
                    status = "✅" if success else "❌"
                    print(f"{status} {theme}")
                
                # Now search within the downloaded filtered data
                print("\nSearching within downloaded data...")
                overture_results = await overture_api.search(SF_BBOX)
                
                if overture_results and any(len(features) > 0 for features in overture_results.values()):
                    print("\nFound features in downloaded data:")
                    
                    # Count features by theme
                    for theme, features in overture_results.items():
                        if not features:
                            continue
                        print(f"\n{theme.title()}:")
                        print(f"  • Total features: {len(features)}")
                else:
                    print("\nNo features found in the downloaded data")
            else:
                print("\nFailed to download any Overture data")
            
            # Download satellite data
            print("\n=== Downloading Sentinel Imagery ===")
            satellite_results = await sentinel_api.download_data(
                bbox=SF_BBOX,
                cloud_cover=10.0,
                bands={
                    "B04": "Red",
                    "B08": "NIR",
                    "B11": "SWIR"
                }
            )
            
            if satellite_results and 'success' in satellite_results:
                print("\nSuccessfully downloaded satellite data:")
                metadata = satellite_results['metadata']
                print(f"- Scene ID: {metadata['scene_id']}")
                print(f"- Date: {metadata['datetime']}")
                print(f"- Cloud cover: {metadata['cloud_cover']}%")
                print(f"- Bands downloaded: {', '.join(metadata['bands_downloaded'])}")
                print(f"- Data directory: {satellite_results['data_dir']}")
            else:
                error_msg = satellite_results.get('error', 'Unknown error')
                print(f"\nFailed to download satellite data: {error_msg}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("\nPlease check your internet connection and try again.")
            return
            
        print("\n🎉 Download complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease check your configuration and try again.")

if __name__ == "__main__":
    # Add project root to Python path
    project_root = str(Path(__file__).parent.parent)
    if project_root not in sys.path:
        print(f"Added {project_root} to Python path")
        sys.path.append(project_root)
    
    import asyncio
    asyncio.run(main()) 