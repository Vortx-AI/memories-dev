"""
Mobile and metaverse data source for 3D and AR/VR applications.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import logging
import json
import numpy as np
import geopandas as gpd
from shapely.geometry import box, Polygon
import trimesh
import pyproj
from PIL import Image
import base64
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MobileMetaverseAPI:
    """Interface for mobile and metaverse data formats."""
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        max_texture_size: int = 2048,
        enable_compression: bool = True
    ):
        """
        Initialize mobile/metaverse data handler.
        
        Args:
            cache_dir: Directory for caching data
            max_texture_size: Maximum texture size for 3D models
            enable_compression: Whether to enable data compression
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".mobile_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_texture_size = max_texture_size
        self.enable_compression = enable_compression
        
        # Supported formats
        self.formats = {
            "3d": ["glb", "gltf", "obj"],
            "ar": ["usdz", "arkit"],
            "vr": ["fbx", "vrm"],
            "terrain": ["heightmap", "terrain"]
        }
    
    def convert_to_3d(
        self,
        vector_data: gpd.GeoDataFrame,
        raster_data: Optional[np.ndarray] = None,
        format: str = "glb",
        attributes: Optional[List[str]] = None,
        height_scale: float = 1.0
    ) -> Dict:
        """
        Convert geospatial data to 3D format.
        
        Args:
            vector_data: Vector data to convert
            raster_data: Optional raster data for texturing
            format: Output format
            attributes: Optional attributes to include
            height_scale: Scale factor for heights
            
        Returns:
            Dictionary containing 3D model data and metadata
        """
        try:
            # Create 3D mesh from vector data
            vertices, faces = self._create_mesh(
                vector_data,
                height_scale=height_scale
            )
            
            # Create mesh object
            mesh = trimesh.Trimesh(
                vertices=vertices,
                faces=faces
            )
            
            # Add texture if raster data is provided
            if raster_data is not None:
                texture = self._create_texture(raster_data)
                mesh.visual.texture = texture
            
            # Add metadata
            metadata = {
                "attributes": self._process_attributes(
                    vector_data,
                    attributes
                ) if attributes else {},
                "bounds": vector_data.total_bounds.tolist(),
                "feature_count": len(vector_data)
            }
            
            # Export to requested format
            output_path = self.cache_dir / f"model.{format}"
            if format == "glb":
                mesh.export(output_path, file_type="glb")
            elif format == "gltf":
                mesh.export(output_path, file_type="gltf")
            elif format == "obj":
                mesh.export(output_path, file_type="obj")
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return {
                "model_path": str(output_path),
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error converting to 3D: {e}")
            raise
    
    def create_ar_scene(
        self,
        models: List[Dict],
        format: str = "usdz",
        scene_scale: float = 1.0,
        include_anchors: bool = True
    ) -> Dict:
        """
        Create an AR scene from 3D models.
        
        Args:
            models: List of 3D models with positions
            format: Output format
            scene_scale: Scale factor for the scene
            include_anchors: Whether to include AR anchors
            
        Returns:
            Dictionary containing AR scene data
        """
        try:
            # Create scene container
            scene = {
                "models": [],
                "anchors": [] if include_anchors else None,
                "metadata": {
                    "format": format,
                    "scale": scene_scale,
                    "model_count": len(models)
                }
            }
            
            for model in models:
                # Process each model
                model_data = self._process_ar_model(
                    model,
                    format=format,
                    scale=scene_scale
                )
                scene["models"].append(model_data)
                
                # Add anchor if enabled
                if include_anchors:
                    anchor = self._create_ar_anchor(model)
                    scene["anchors"].append(anchor)
            
            # Export scene
            output_path = self.cache_dir / f"scene.{format}"
            with open(output_path, "w") as f:
                json.dump(scene, f)
            
            return {
                "scene_path": str(output_path),
                "metadata": scene["metadata"]
            }
            
        except Exception as e:
            logger.error(f"Error creating AR scene: {e}")
            raise
    
    def create_terrain_model(
        self,
        elevation_data: np.ndarray,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        resolution: float,
        format: str = "heightmap",
        vertical_exaggeration: float = 1.0
    ) -> Dict:
        """
        Create terrain model from elevation data.
        
        Args:
            elevation_data: Elevation array
            bbox: Bounding box or Polygon
            resolution: Spatial resolution
            format: Output format
            vertical_exaggeration: Vertical exaggeration factor
            
        Returns:
            Dictionary containing terrain model
        """
        try:
            # Process elevation data
            processed_elevation = self._process_elevation(
                elevation_data,
                vertical_exaggeration
            )
            
            # Create terrain model based on format
            if format == "heightmap":
                model = self._create_heightmap(
                    processed_elevation,
                    resolution
                )
            elif format == "terrain":
                model = self._create_terrain_mesh(
                    processed_elevation,
                    bbox,
                    resolution
                )
            else:
                raise ValueError(f"Unsupported terrain format: {format}")
            
            # Add metadata
            metadata = {
                "format": format,
                "resolution": resolution,
                "bbox": bbox if isinstance(bbox, tuple) else bbox.bounds,
                "vertical_exaggeration": vertical_exaggeration,
                "elevation_range": [
                    float(processed_elevation.min()),
                    float(processed_elevation.max())
                ]
            }
            
            return {
                "model": model,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error creating terrain model: {e}")
            raise
    
    def optimize_for_mobile(
        self,
        model_data: Dict,
        target_size: str = "medium",
        preserve_attributes: Optional[List[str]] = None
    ) -> Dict:
        """
        Optimize 3D model for mobile devices.
        
        Args:
            model_data: Input model data
            target_size: Target size category (small, medium, large)
            preserve_attributes: Attributes to preserve
            
        Returns:
            Dictionary containing optimized model
        """
        try:
            # Load model
            model_path = model_data["model_path"]
            mesh = trimesh.load(model_path)
            
            # Define optimization parameters
            params = self._get_optimization_params(target_size)
            
            # Simplify mesh
            simplified = mesh.simplify_quadratic_decimation(
                params["target_faces"]
            )
            
            # Optimize textures
            if hasattr(simplified.visual, "texture"):
                simplified.visual.texture = self._optimize_texture(
                    simplified.visual.texture,
                    params["max_texture_size"]
                )
            
            # Preserve specified attributes
            if preserve_attributes and "metadata" in model_data:
                preserved = {
                    attr: model_data["metadata"]["attributes"][attr]
                    for attr in preserve_attributes
                    if attr in model_data["metadata"]["attributes"]
                }
                metadata = {
                    **model_data["metadata"],
                    "attributes": preserved
                }
            else:
                metadata = model_data["metadata"]
            
            # Export optimized model
            output_path = Path(model_path).parent / f"optimized_{target_size}.glb"
            simplified.export(output_path)
            
            return {
                "model_path": str(output_path),
                "metadata": {
                    **metadata,
                    "optimization": {
                        "target_size": target_size,
                        "original_faces": len(mesh.faces),
                        "optimized_faces": len(simplified.faces)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error optimizing model: {e}")
            raise
    
    def _create_mesh(
        self,
        vector_data: gpd.GeoDataFrame,
        height_scale: float = 1.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Create 3D mesh from vector data."""
        # Extract coordinates and triangulate
        coords = []
        faces = []
        
        for geom in vector_data.geometry:
            if hasattr(geom, "exterior"):
                # Process polygon
                exterior_coords = np.array(geom.exterior.coords)
                base_idx = len(coords)
                
                # Add base vertices
                coords.extend(exterior_coords)
                
                # Add top vertices (with height)
                height = height_scale * (
                    vector_data.loc[vector_data.geometry == geom, "height"].iloc[0]
                    if "height" in vector_data.columns
                    else 1.0
                )
                coords.extend(
                    exterior_coords + np.array([0, 0, height])
                )
                
                # Create faces
                n_points = len(exterior_coords) - 1
                for i in range(n_points):
                    # Add side faces
                    faces.append([
                        base_idx + i,
                        base_idx + (i + 1) % n_points,
                        base_idx + n_points + i
                    ])
                    faces.append([
                        base_idx + n_points + i,
                        base_idx + (i + 1) % n_points,
                        base_idx + n_points + (i + 1) % n_points
                    ])
        
        return np.array(coords), np.array(faces)
    
    def _create_texture(self, raster_data: np.ndarray) -> Image.Image:
        """Create texture from raster data."""
        if raster_data.ndim == 2:
            # Single band - convert to RGB
            raster_data = np.stack([raster_data] * 3, axis=-1)
        elif raster_data.ndim == 3 and raster_data.shape[2] > 3:
            # More than 3 bands - use first 3
            raster_data = raster_data[:, :, :3]
        
        # Normalize and convert to 8-bit
        raster_data = ((raster_data - raster_data.min()) /
                      (raster_data.max() - raster_data.min()) * 255).astype(np.uint8)
        
        return Image.fromarray(raster_data)
    
    def _process_attributes(
        self,
        vector_data: gpd.GeoDataFrame,
        attributes: List[str]
    ) -> Dict:
        """Process and format attributes."""
        result = {}
        for attr in attributes:
            if attr in vector_data.columns:
                values = vector_data[attr].tolist()
                result[attr] = {
                    "values": values,
                    "type": str(vector_data[attr].dtype),
                    "unique_count": len(set(values))
                }
        return result
    
    def _process_ar_model(
        self,
        model: Dict,
        format: str,
        scale: float
    ) -> Dict:
        """Process model for AR scene."""
        # Load model
        mesh = trimesh.load(model["model_path"])
        
        # Scale model
        mesh.apply_scale(scale)
        
        # Convert to requested format
        if format == "usdz":
            # Export as USDZ for iOS
            output_path = self.cache_dir / f"{Path(model['model_path']).stem}.usdz"
            mesh.export(output_path)
        elif format == "arkit":
            # Export as reality file for ARKit
            output_path = self.cache_dir / f"{Path(model['model_path']).stem}.reality"
            mesh.export(output_path)
        
        return {
            "path": str(output_path),
            "position": model.get("position", [0, 0, 0]),
            "rotation": model.get("rotation", [0, 0, 0]),
            "scale": scale
        }
    
    def _create_ar_anchor(self, model: Dict) -> Dict:
        """Create AR anchor for a model."""
        return {
            "type": "plane",
            "position": model.get("position", [0, 0, 0]),
            "rotation": model.get("rotation", [0, 0, 0]),
            "size": [1.0, 1.0]  # Default plane size
        }
    
    def _process_elevation(
        self,
        elevation: np.ndarray,
        vertical_exaggeration: float
    ) -> np.ndarray:
        """Process elevation data."""
        # Apply vertical exaggeration
        processed = elevation * vertical_exaggeration
        
        # Fill missing values
        if np.ma.is_masked(processed):
            processed = np.ma.filled(processed, np.ma.median(processed))
        
        return processed
    
    def _create_heightmap(
        self,
        elevation: np.ndarray,
        resolution: float
    ) -> Dict:
        """Create heightmap from elevation data."""
        # Normalize to 0-1 range
        normalized = (elevation - elevation.min()) / (elevation.max() - elevation.min())
        
        # Convert to image
        heightmap = Image.fromarray((normalized * 255).astype(np.uint8))
        
        # Save heightmap
        output_path = self.cache_dir / "heightmap.png"
        heightmap.save(output_path)
        
        return {
            "path": str(output_path),
            "resolution": resolution,
            "min_height": float(elevation.min()),
            "max_height": float(elevation.max())
        }
    
    def _create_terrain_mesh(
        self,
        elevation: np.ndarray,
        bbox: Union[Tuple[float, float, float, float], Polygon],
        resolution: float
    ) -> Dict:
        """Create terrain mesh from elevation data."""
        # Create grid
        y, x = np.mgrid[0:elevation.shape[0], 0:elevation.shape[1]]
        
        # Scale to real-world coordinates
        if isinstance(bbox, tuple):
            minx, miny, maxx, maxy = bbox
        else:
            minx, miny, maxx, maxy = bbox.bounds
        
        x = minx + x * resolution
        y = miny + y * resolution
        
        # Create vertices
        vertices = np.column_stack((
            x.flatten(),
            y.flatten(),
            elevation.flatten()
        ))
        
        # Create faces
        faces = []
        rows, cols = elevation.shape
        for i in range(rows - 1):
            for j in range(cols - 1):
                idx = i * cols + j
                faces.extend([
                    [idx, idx + 1, idx + cols],
                    [idx + 1, idx + cols + 1, idx + cols]
                ])
        
        # Create mesh
        mesh = trimesh.Trimesh(
            vertices=vertices,
            faces=faces
        )
        
        # Export mesh
        output_path = self.cache_dir / "terrain.glb"
        mesh.export(output_path)
        
        return {
            "path": str(output_path),
            "resolution": resolution,
            "vertex_count": len(vertices),
            "face_count": len(faces)
        }
    
    def _get_optimization_params(self, target_size: str) -> Dict:
        """Get optimization parameters for target size."""
        params = {
            "small": {
                "target_faces": 5000,
                "max_texture_size": 512
            },
            "medium": {
                "target_faces": 10000,
                "max_texture_size": 1024
            },
            "large": {
                "target_faces": 20000,
                "max_texture_size": 2048
            }
        }
        
        if target_size not in params:
            raise ValueError(f"Invalid target size: {target_size}")
        
        return params[target_size]
    
    def _optimize_texture(
        self,
        texture: Image.Image,
        max_size: int
    ) -> Image.Image:
        """Optimize texture for target size."""
        # Get current size
        width, height = texture.size
        
        # Calculate new size
        if width > max_size or height > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            # Resize texture
            texture = texture.resize(
                (new_width, new_height),
                Image.LANCZOS
            )
        
        return texture 