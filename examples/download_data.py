#!/usr/bin/env python3
"""
Example script demonstrating data download using Overture and Sentinel APIs.
Uses direct HTTP downloads for Overture data - no AWS CLI required.
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
    
    try:
        # Initialize config with correct path
        project_root = Path(__file__).parent.parent
        config_path = project_root / "memories" / "config" / "config.yaml"
        config = Config(config_path=str(config_path))
        
        # Create directories
        setup_directories(config)
        
        # Get paths from config
        paths = config.config['data_acquisition']['paths']
        
        try:
            # Initialize APIs with config paths - use AWS for Overture
            print("\n=== Downloading Overture Maps Data from AWS S3 ===")
            print("Note: Using direct HTTP downloads - no AWS CLI required")
            
            overture_api = OvertureAPI(data_dir=paths['overture'], use_azure=False)
            sentinel_api = SentinelAPI(data_dir=paths['satellite'])
            
            # First download the data
            download_results = overture_api.download_data(SF_BBOX)
            
            if any(download_results.values()):
                print("\nSuccessfully downloaded Overture data from AWS:")
                for theme, success in download_results.items():
                    status = "✅" if success else "❌"
                    print(f"{status} {theme}")
                
                # Now search within the downloaded data
                print("\nSearching within downloaded data...")
                overture_results = await overture_api.search(SF_BBOX)
                
                if overture_results and any(len(features) > 0 for features in overture_results.values()):
                    print("\nFound features in downloaded data:")
                    
                    # Count features by theme and type
                    theme_counts = {}
                    for theme, features in overture_results.items():
                        if not features:
                            continue
                            
                        theme_counts[theme] = {
                            'total': len(features),
                            'types': {}
                        }
                        
                        # Count subtypes within each theme
                        for feature in features:
                            if theme == 'buildings':
                                btype = feature.get('building_type', 'unknown')
                                theme_counts[theme]['types'][btype] = theme_counts[theme]['types'].get(btype, 0) + 1
                            elif theme == 'places':
                                ptype = feature.get('place_type', 'unknown')
                                theme_counts[theme]['types'][ptype] = theme_counts[theme]['types'].get(ptype, 0) + 1
                            elif theme == 'transportation':
                                rtype = feature.get('road_type', 'unknown')
                                theme_counts[theme]['types'][rtype] = theme_counts[theme]['types'].get(rtype, 0) + 1
                    
                    # Print theme statistics
                    print("\nFeature counts by theme:")
                    for theme, counts in theme_counts.items():
                        print(f"\n{theme.title()}:")
                        print(f"  • Total: {counts['total']}")
                        if counts['types']:
                            print("  • Types:")
                            for type_name, type_count in counts['types'].items():
                                print(f"    - {type_name}: {type_count}")
                else:
                    print("\nNo features found in the downloaded data")
            else:
                print("\nFailed to download any Overture data from AWS")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("\nPlease check your internet connection and try again.")
            return
            
        # Download satellite data
        print("\n=== Downloading Satellite Imagery ===")
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
    
    asyncio.run(main()) 