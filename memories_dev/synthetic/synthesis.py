from typing import List, Dict, Any, Optional, Union
import numpy as np
import torch
import rasterio
from datetime import datetime
from pathlib import Path
from .memory import EarthMemoryEncoder, EarthMemoryStore

class DataSource:
    """Base class for different earth observation data sources."""
    
    def __init__(self, name: str, resolution: float):
        self.name = name
        self.resolution = resolution  # in meters
        
    def load_data(
        self,
        coordinates: tuple,
        timestamp: datetime,
        window_size: tuple = (256, 256)
    ) -> np.ndarray:
        """Load data for given coordinates and time."""
        raise NotImplementedError
        
    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Preprocess the loaded data."""
        raise NotImplementedError

class SatelliteDataSource(DataSource):
    """Handler for satellite imagery data."""
    
    def __init__(
        self,
        name: str,
        resolution: float,
        bands: List[str],
        data_path: Path
    ):
        super().__init__(name, resolution)
        self.bands = bands
        self.data_path = Path(data_path)
        
    def load_data(
        self,
        coordinates: tuple,
        timestamp: datetime,
        window_size: tuple = (256, 256)
    ) -> np.ndarray:
        """Load satellite data for the given parameters."""
        # Find closest image in time
        image_path = self._find_closest_image(coordinates, timestamp)
        
        with rasterio.open(image_path) as src:
            # Calculate pixel coordinates
            py, px = src.index(*coordinates)
            
            # Read window around coordinates
            half_h, half_w = window_size[0]//2, window_size[1]//2
            window = rasterio.windows.Window(
                px - half_w, py - half_h,
                window_size[0], window_size[1]
            )
            
            data = src.read(window=window)
            
        return data
    
    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Preprocess satellite imagery."""
        # Normalize to [0, 1]
        data = data.astype(np.float32)
        data = (data - data.min()) / (data.max() - data.min() + 1e-8)
        return data
    
    def _find_closest_image(self, coordinates: tuple, timestamp: datetime) -> Path:
        """Find the image closest to the given timestamp."""
        # Implementation depends on data organization
        # This is a placeholder
        return self.data_path / "example_image.tif"

class SynthesisPipeline:
    """Pipeline for synthesizing multiple data sources into memory embeddings."""
    
    def __init__(
        self,
        data_sources: List[DataSource],
        memory_store: EarthMemoryStore,
        window_size: tuple = (256, 256)
    ):
        self.data_sources = data_sources
        self.memory_store = memory_store
        self.window_size = window_size
        
    def process_location(
        self,
        coordinates: tuple,
        timestamp: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a location across all data sources and store as memory.
        
        Args:
            coordinates: (latitude, longitude) tuple
            timestamp: Time of observation
            metadata: Additional metadata
            
        Returns:
            Dictionary containing processed data and memory embedding
        """
        combined_data = []
        combined_metadata = metadata or {}
        
        # Collect data from all sources
        for source in self.data_sources:
            try:
                data = source.load_data(coordinates, timestamp, self.window_size)
                data = source.preprocess(data)
                combined_data.append(data)
                
                # Add source-specific metadata
                combined_metadata[f"{source.name}_resolution"] = source.resolution
                
            except Exception as e:
                print(f"Error processing source {source.name}: {str(e)}")
                continue
                
        if not combined_data:
            raise ValueError("No data could be processed from any source")
            
        # Stack all data sources
        combined_array = np.concatenate(combined_data, axis=0)
        
        # Convert to tensor and get memory embedding
        data_tensor = torch.from_numpy(combined_array).float()
        data_tensor = data_tensor.unsqueeze(0).unsqueeze(0)  # Add batch and temporal dims
        
        embedding = self.memory_store.encoder(data_tensor)
        
        # Store in memory
        self.memory_store.store_memory(
            embedding=embedding,
            coordinates=coordinates,
            timestamp=timestamp,
            metadata=combined_metadata
        )
        
        return {
            "embedding": embedding,
            "data": combined_array,
            "metadata": combined_metadata
        }
    
    def process_time_series(
        self,
        coordinates: tuple,
        time_range: tuple,
        interval_days: int = 1
    ) -> List[Dict[str, Any]]:
        """Process a location across a time range."""
        start_time, end_time = time_range
        current_time = start_time
        
        results = []
        while current_time <= end_time:
            try:
                result = self.process_location(coordinates, current_time)
                results.append(result)
            except Exception as e:
                print(f"Error processing time {current_time}: {str(e)}")
                
            current_time += datetime.timedelta(days=interval_days)
            
        return results 