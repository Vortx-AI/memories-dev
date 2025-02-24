"""
Tools for location processing that can be used .
"""

from typing import Dict, Any, List, Tuple, Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import logging

logger = logging.getLogger(__name__)

def filter_by_distance(locations: List[Dict[str, Any]], center: Tuple[float, float], radius_km: float) -> List[Dict[str, Any]]:
    """
    Filter locations within a certain radius of a center point.
    
    Args:
        locations: List of location dictionaries with lat/lon coordinates
        center: Tuple of (latitude, longitude) for center point
        radius_km: Radius in kilometers to search within
        
    Returns:
        List of locations within the radius
    """
    from geopy.distance import geodesic
    
    filtered = []
    center_point = center
    
    for loc in locations:
        if 'coordinates' not in loc:
            continue
            
        loc_point = loc['coordinates']
        distance = geodesic(center_point, loc_point).kilometers
        
        if distance <= radius_km:
            loc['distance_km'] = round(distance, 2)
            filtered.append(loc)
    
    return filtered

def filter_by_type(locations: List[Dict[str, Any]], location_types: List[str]) -> List[Dict[str, Any]]:
    """
    Filter locations by their type.
    
    Args:
        locations: List of location dictionaries
        location_types: List of location types to include
        
    Returns:
        Filtered list of locations
    """
    return [loc for loc in locations if loc.get('type') in location_types]

def sort_locations_by_distance(locations: List[Dict[str, Any]], 
                             reference_point: Tuple[float, float]) -> List[Dict[str, Any]]:
    """
    Sort locations by distance from a reference point.
    
    Args:
        locations: List of location dictionaries with lat/lon coordinates
        reference_point: Tuple of (latitude, longitude) to measure distance from
        
    Returns:
        Sorted list of locations with distances added
    """
    from geopy.distance import geodesic
    
    # Add distances
    for loc in locations:
        if 'coordinates' in loc:
            distance = geodesic(reference_point, loc['coordinates']).kilometers
            loc['distance_km'] = round(distance, 2)
    
    # Sort by distance
    return sorted(locations, key=lambda x: x.get('distance_km', float('inf')))

def get_bounding_box(locations: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate the bounding box containing all locations.
    
    Args:
        locations: List of location dictionaries with lat/lon coordinates
        
    Returns:
        Dictionary with min/max lat/lon values
    """
    if not locations:
        return {}
        
    lats = []
    lons = []
    
    for loc in locations:
        if 'coordinates' in loc:
            lat, lon = loc['coordinates']
            lats.append(lat)
            lons.append(lon)
    
    if not lats or not lons:
        return {}
        
    return {
        'min_lat': min(lats),
        'max_lat': max(lats),
        'min_lon': min(lons),
        'max_lon': max(lons)
    }

def cluster_locations(locations: List[Dict[str, Any]], max_distance_km: float) -> List[List[Dict[str, Any]]]:
    """
    Cluster locations that are within max_distance_km of each other.
    
    Args:
        locations: List of location dictionaries with lat/lon coordinates
        max_distance_km: Maximum distance between points in a cluster
        
    Returns:
        List of clusters, where each cluster is a list of locations
    """
    from geopy.distance import geodesic
    from sklearn.cluster import DBSCAN
    import numpy as np
    
    if not locations:
        return []
    
    # Extract coordinates
    coords = []
    for loc in locations:
        if 'coordinates' in loc:
            coords.append(loc['coordinates'])
    
    if not coords:
        return []
    
    # Convert to numpy array
    X = np.array(coords)
    
    # Cluster using DBSCAN
    db = DBSCAN(eps=max_distance_km/111.32, min_samples=1, metric='haversine')
    cluster_labels = db.fit_predict(X)
    
    # Group locations by cluster
    clusters = {}
    for i, label in enumerate(cluster_labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(locations[i])
    
    return list(clusters.values()) 