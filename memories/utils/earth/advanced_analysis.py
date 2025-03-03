"""
Advanced analysis module for processing and analyzing Earth observation data.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
from memories.utils.earth.raster_processor import RasterTileProcessor
from memories.utils.earth.vector_processor import VectorTileProcessor
from memories.utils.processors.comp import calculate_ndvi, transformer_process
from memories.utils.types import Bounds, ImageType, RasterType, VectorType
from shapely.geometry import Point, Polygon


class AdvancedAnalysis:
    """Advanced analysis tools for Earth observation data"""
    
    def __init__(self):
        """Initialize analysis tools"""
        self.raster_processor = RasterTileProcessor()
        self.vector_processor = None  # Initialize when needed with bounds
        
    def analyze_vegetation(
        self,
        bounds: Bounds,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze vegetation indices and patterns.
        
        Args:
            bounds: Geographic bounds for analysis
            time_range: Optional time range filter
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Get raster data
            raster_data = self.raster_processor.process_tile(
                bounds,
                format='raw',
                transformations=['normalize']
            )
            
            # Calculate NDVI
            ndvi = calculate_ndvi(raster_data)
            
            # Analyze vegetation patterns
            results = {
                'ndvi_mean': float(np.mean(ndvi)),
                'ndvi_std': float(np.std(ndvi)),
                'vegetation_coverage': float(np.sum(ndvi > 0.3) / ndvi.size),
                'bounds': bounds
            }
            
            return results
            
        except Exception as e:
            raise Exception(f"Error in vegetation analysis: {str(e)}")
            
    def analyze_urban_patterns(
        self,
        bounds: Bounds,
        layers: List[str] = ['buildings', 'roads']
    ) -> Dict[str, Any]:
        """
        Analyze urban development patterns.
        
        Args:
            bounds: Geographic bounds for analysis
            layers: Vector layers to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Initialize vector processor if needed
            if self.vector_processor is None:
                self.vector_processor = VectorTileProcessor(bounds=bounds, layers=layers)
            
            # Get vector data
            vector_data = self.vector_processor.process_tile(bounds)
            
            # Calculate urban metrics
            building_density = len(vector_data) / (
                (bounds.east - bounds.west) * (bounds.north - bounds.south)
            )
            
            # Analyze patterns
            results = {
                'building_density': building_density,
                'building_count': len(vector_data),
                'bounds': bounds
            }
            
            return results
            
        except Exception as e:
            raise Exception(f"Error in urban pattern analysis: {str(e)}")
            
    def analyze_change(
        self,
        bounds: Bounds,
        start_time: str,
        end_time: str
    ) -> Dict[str, Any]:
        """
        Analyze changes between two time periods.
        
        Args:
            bounds: Geographic bounds for analysis
            start_time: Start time for analysis
            end_time: End time for analysis
            
        Returns:
            Dictionary containing change analysis results
        """
        try:
            # Get data for both time periods
            start_data = self.raster_processor.process_tile(
                bounds,
                format='raw',
                time=start_time
            )
            
            end_data = self.raster_processor.process_tile(
                bounds,
                format='raw',
                time=end_time
            )
            
            # Calculate changes
            difference = end_data - start_data
            
            # Analyze changes
            results = {
                'mean_change': float(np.mean(difference)),
                'std_change': float(np.std(difference)),
                'change_magnitude': float(np.sum(np.abs(difference))),
                'bounds': bounds,
                'time_range': [start_time, end_time]
            }
            
            return results
            
        except Exception as e:
            raise Exception(f"Error in change analysis: {str(e)}")
            
    def generate_report(
        self,
        bounds: Bounds,
        analyses: List[str] = ['vegetation', 'urban', 'change']
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analysis report.
        
        Args:
            bounds: Geographic bounds for analysis
            analyses: List of analyses to include
            
        Returns:
            Dictionary containing complete analysis report
        """
        report = {'bounds': bounds, 'timestamp': pd.Timestamp.now().isoformat()}
        
        try:
            # Run requested analyses
            if 'vegetation' in analyses:
                report['vegetation'] = self.analyze_vegetation(bounds)
                
            if 'urban' in analyses:
                report['urban'] = self.analyze_urban_patterns(bounds)
                
            if 'change' in analyses:
                report['change'] = self.analyze_change(
                    bounds,
                    start_time='2020-01-01',
                    end_time='2023-01-01'
                )
                
            return report
            
        except Exception as e:
            raise Exception(f"Error generating report: {str(e)}") 