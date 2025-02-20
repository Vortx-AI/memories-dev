"""
Overture Maps local data processing and download functionality.
"""

import os
from pathlib import Path
import json
import pandas as pd
import pyarrow.parquet as pq
import duckdb
from typing import Dict, List, Any, Union, Tuple, Optional
from shapely.geometry import box, Polygon

# Define ALL possible themes and their columns
ALL_THEMES = {
    'buildings': """
        id,
        type as building_type,
        height,
        bbox.xmin,
        bbox.ymin,
        bbox.xmax,
        bbox.ymax,
        geometry
    """,
    'places': """
        id,
        type as place_type,
        confidence,
        bbox.xmin,
        bbox.ymin,
        bbox.xmax,
        bbox.ymax,
        geometry
    """,
    'transportation': """
        id,
        type as road_type,
        bbox.xmin,
        bbox.ymin,
        bbox.xmax,
        bbox.ymax,
        geometry
    """
}

def get_overture_data(
    bbox: Optional[Union[Tuple[float, float, float, float], List[float], Polygon]] = None,
    themes: Optional[List[str]] = None,
    save_path: str = "./overture_data"
) -> Dict[str, bool]:
    """
    Download Overture data for specific bbox and/or themes.
    
    Args:
        bbox: Optional bounding box as (west, south, east, north) or Polygon
        themes: Optional list of themes to download. If None, downloads all themes
        save_path: Base directory to save the data
        
    Returns:
        Dictionary containing download status for each theme
    """
    print("Downloading Overture data...")
    
    # Use all themes if none specified
    if themes is None or "all" in themes:
        themes = list(ALL_THEMES.keys())
    
    # Validate themes
    themes = [theme for theme in themes if theme in ALL_THEMES]
    if not themes:
        raise ValueError("No valid themes specified")
    
    # Convert bbox to dictionary format
    if bbox is not None:
        if isinstance(bbox, (tuple, list)):
            bbox_dict = {
                'xmin': bbox[0],
                'ymin': bbox[1],
                'xmax': bbox[2],
                'ymax': bbox[3]
            }
        elif isinstance(bbox, Polygon):
            bounds = bbox.bounds
            bbox_dict = {
                'xmin': bounds[0],
                'ymin': bounds[1],
                'xmax': bounds[2],
                'ymax': bounds[3]
            }
        else:
            raise ValueError("bbox must be tuple/list of coordinates or Polygon")
    else:
        # Default to San Francisco if no bbox specified
        bbox_dict = {
            'xmin': -122.4018,
            'ymin': 37.7914,
            'xmax': -122.3928,
            'ymax': 37.7994
        }
    
    # Create base directory
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize DuckDB connection
    con = duckdb.connect(database=":memory:")
    
    try:
        # Install and load extensions
        con.execute("INSTALL azure;")
        con.execute("LOAD azure;")
        con.execute("INSTALL spatial;")
        con.execute("LOAD spatial;")
        
        # Set up Azure connection with SSL verification disabled for testing
        con.execute("""
            SET azure_storage_connection_string = 'DefaultEndpointsProtocol=https;AccountName=overturemapswestus2;EndpointSuffix=core.windows.net';
            SET azure_storage_verify_ssl = false;
        """)
        
        # Set latest Overture release
        OVERTURE_RELEASE = "2025-01-22.0"
        
        results = {}
        
        # Download each theme
        for theme in themes:
            print(f"\nDownloading {theme}...")
            theme_dir = save_path / theme
            theme_dir.mkdir(parents=True, exist_ok=True)
            output_file = theme_dir / f"{theme}.geojsonseq"
            
            try:
                # Create optimized query with bbox filter
                query = f"""
                COPY (
                    SELECT
                        {ALL_THEMES[theme]}
                    FROM read_parquet(
                        'azure://release/{OVERTURE_RELEASE}/theme={theme}/type=*/*',
                        filename=true,
                        hive_partitioning=1
                    )
                    WHERE bbox.xmin >= {bbox_dict['xmin']}
                    AND bbox.xmin <= {bbox_dict['xmax']}
                    AND bbox.ymin >= {bbox_dict['ymin']}
                    AND bbox.ymin <= {bbox_dict['ymax']}
                    LIMIT 1000  -- Limit features per theme
                ) TO '{output_file}' WITH (FORMAT GDAL, DRIVER 'GeoJSONSeq');
                """
                
                # Execute query with optimized settings
                con.execute("SET memory_limit='1GB';")
                con.execute("SET threads=4;")
                con.execute(query)
                
                results[theme] = True
                print(f"Successfully downloaded {theme} data")
                
            except Exception as e:
                print(f"Error downloading {theme}: {str(e)}")
                results[theme] = False
    
    finally:
        con.close()
    
    return results

def get_specific_themes(theme_list: List[str]) -> List[str]:
    """
    Get specific themes from ALL_THEMES.
    
    Args:
        theme_list: List of themes to include
        
    Returns:
        List of valid theme names
    """
    return [
        theme for theme in theme_list
        if theme in ALL_THEMES or theme == "all"
    ]

def index_overture_parquet(base_path: str = "./overture_data") -> Dict[str, List[str]]:
    """
    Analyze Overture local parquet files and record any processing errors.
    
    Args:
        base_path (str): Base directory containing Overture parquet files
        
    Returns:
        Dict containing lists of processed and error files
    """
    # Convert base_path to Path object
    base_path = Path(base_path)
    
    # Set up data directory path relative to project root
    data_dir = Path(__file__).parents[3] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "processed_files": [],
        "error_files": []
    }
    
    # Walk through all files in the directory
    for root, _, files in os.walk(base_path):
        for file_name in files:
            if file_name.endswith('.parquet'):
                file_path = Path(root) / file_name
                
                try:
                    # Try reading the parquet file
                    table = pq.read_table(str(file_path))
                    results["processed_files"].append({
                        "file_name": file_name,
                        "file_path": str(file_path)
                    })
                except Exception as e:
                    results["error_files"].append({
                        "file_name": file_name,
                        "file_path": str(file_path),
                        "error": str(e)
                    })
                    print(f"Error processing {file_name}: {str(e)}")
    
    # Save results to JSON file in project's data directory
    output_path = data_dir / "overture_parquet_index.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nAnalysis saved to: {output_path}")
    
    # Print summary
    print("\nSummary:")
    print(f"Total processed files: {len(results['processed_files'])}")
    print(f"Total error files: {len(results['error_files'])}")
    
    return results

if __name__ == "__main__":
    # Example usage
    bbox = (-122.4018, 37.7914, -122.3928, 37.7994)  # San Francisco area
    
    # Download all themes
    results = get_overture_data(bbox=bbox)
    print("\nDownload results for all themes:")
    for theme, success in results.items():
        print(f"{theme}: {'✓' if success else '✗'}")
    
    # Download specific themes
    specific_themes = get_specific_themes(['buildings', 'places'])
    results = get_overture_data(bbox=bbox, themes=specific_themes)
    print("\nDownload results for specific themes:")
    for theme, success in results.items():
        print(f"{theme}: {'✓' if success else '✗'}")
    
    # Run the analysis
    error_details = index_overture_parquet()
