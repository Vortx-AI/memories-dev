#!/usr/bin/env python3
"""
Script to download Overture data for a small area in San Francisco.
Uses optimized DuckDB queries.
"""

import os
import sys
import shutil
import duckdb
from pathlib import Path
from datetime import datetime, timedelta

# Overture release
OVERTURE_RELEASE = "2025-01-22.0"

# San Francisco Financial District (1km x 1km)
SF_BBOX = {
    'xmin': -122.4018,  # Approximately Market & Montgomery
    'ymin': 37.7914,
    'xmax': -122.3928,  # About 1km east
    'ymax': 37.7994     # About 1km north
}

# Themes to download with their specific columns
THEMES = {
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

# Directory structure within examples
EXAMPLES_DIR = Path("examples")
DATA_DIR = EXAMPLES_DIR / "data/overture"
CONFIG_DIR = EXAMPLES_DIR / "config"

def setup_directories():
    """Set up necessary directories."""
    # Create config directory
    config_dir = CONFIG_DIR
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create data directory
    data_dir = DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

def download_theme(con, theme, columns):
    """Download a theme from Azure using DuckDB.
    
    Args:
        con: DuckDB connection
        theme: Theme name
        columns: Columns to select
    """
    theme_dir = DATA_DIR / theme
    theme_dir.mkdir(parents=True, exist_ok=True)
    output_file = theme_dir / f"{theme}.geojsonseq"
    
    # Remove existing file if it exists
    if output_file.exists():
        print(f"Removing existing file: {output_file}")
        output_file.unlink()
    
    print(f"Downloading {theme} data...")
    
    try:
        # Create optimized query with index hint and feature limit
        query = f"""
        COPY (
            SELECT
                {columns}
            FROM read_parquet(
                'azure://release/{OVERTURE_RELEASE}/theme={theme}/type=*/*',
                filename=true,
                hive_partitioning=1
            )
            WHERE bbox.xmin >= {SF_BBOX['xmin']}
            AND bbox.xmin <= {SF_BBOX['xmax']}
            AND bbox.ymin >= {SF_BBOX['ymin']}
            AND bbox.ymin <= {SF_BBOX['ymax']}
            LIMIT 100  -- Limit to 100 features per category
        ) TO '{output_file}' WITH (FORMAT GDAL, DRIVER 'GeoJSONSeq');
        """
        
        # Execute query with optimized memory settings
        con.execute("SET memory_limit='1GB';")  # Reduced memory limit
        con.execute("SET threads=4;")  # Limit thread usage
        con.execute(query)
        print(f"Successfully downloaded {theme} data to {output_file}")
        
    except Exception as e:
        print(f"Error downloading {theme} data: {e}")

def main():
    """Main function to download Overture data."""
    print("=== Downloading Overture Maps Data ===")
    
    # Set up directories
    setup_directories()
    
    # Create DuckDB connection with optimized settings
    con = duckdb.connect(database=":memory:")
    
    try:
        # Install and load extensions
        con.execute("INSTALL azure;")
        con.execute("LOAD azure;")
        con.execute("INSTALL spatial;")
        con.execute("LOAD spatial;")
        
        # Set up Azure connection
        con.execute("""
            SET azure_storage_connection_string = 'DefaultEndpointsProtocol=https;AccountName=overturemapswestus2;EndpointSuffix=core.windows.net';
        """)
        
        # Download themes sequentially (more stable than parallel)
        for theme, columns in THEMES.items():
            print(f"\nDownloading {theme}...")
            download_theme(con, theme, columns)
    finally:
        con.close()
    
    print("\n🎉 Download complete!")
    print(f"Data stored in: {DATA_DIR}")

if __name__ == "__main__":
    main() 