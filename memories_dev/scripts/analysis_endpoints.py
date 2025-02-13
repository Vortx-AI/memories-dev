from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path

from ..core.memory import EarthMemoryStore
from ..core.synthesis import SynthesisPipeline
from ..core.data_sources import (
    SatelliteDataSource,
    WeatherDataSource,
    ElevationDataSource,
    LandUseDataSource,
    ClimateDataSource
)

router = APIRouter(prefix="/analysis", tags=["analysis"])

# Initialize services with all data sources
memory_store = EarthMemoryStore(Path("/app/data/memories"))

data_sources = [
    SatelliteDataSource(
        name="sentinel2",
        resolution=10.0,
        bands=["B02", "B03", "B04", "B08"],
        data_path=Path("/app/data/satellite")
    ),
    WeatherDataSource(
        name="weather",
        resolution=1000.0,
        api_key=None  # Set from environment
    ),
    ElevationDataSource(
        name="elevation",
        resolution=30.0,
        data_path=Path("/app/data/elevation")
    ),
    LandUseDataSource(
        name="landuse",
        resolution=100.0,
        data_path=Path("/app/data/landuse")
    ),
    ClimateDataSource(
        name="climate",
        resolution=25000.0,
        data_path=Path("/app/data/climate")
    )
]

pipeline = SynthesisPipeline(
    data_sources=data_sources,
    memory_store=memory_store
)

class ChangeDetectionRequest(BaseModel):
    """Request for detecting environmental changes."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    start_time: datetime
    end_time: datetime
    interval_days: int = Field(default=30)
    change_threshold: float = Field(default=0.1)

@router.post("/detect_changes")
async def detect_environmental_changes(request: ChangeDetectionRequest):
    """Detect and analyze environmental changes over time."""
    try:
        # Process time series data
        results = pipeline.process_time_series(
            coordinates=(request.latitude, request.longitude),
            time_range=(request.start_time, request.end_time),
            interval_days=request.interval_days
        )
        
        # Analyze changes
        changes = []
        for i in range(1, len(results)):
            prev_data = results[i-1]["data"]
            curr_data = results[i]["data"]
            
            # Calculate change metrics
            diff = np.mean(np.abs(curr_data - prev_data))
            if diff > request.change_threshold:
                changes.append({
                    "timestamp": results[i]["metadata"]["timestamp"],
                    "change_magnitude": float(diff),
                    "previous_state": results[i-1]["metadata"],
                    "current_state": results[i]["metadata"]
                })
        
        return {
            "status": "success",
            "total_intervals": len(results),
            "significant_changes": changes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SimilarityRequest(BaseModel):
    """Request for finding similar locations."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: datetime
    radius_km: float = Field(default=100.0)
    limit: int = Field(default=5)

@router.post("/find_similar")
async def find_similar_locations(request: SimilarityRequest):
    """Find locations with similar environmental characteristics."""
    try:
        # Process reference location
        reference = pipeline.process_location(
            coordinates=(request.latitude, request.longitude),
            timestamp=request.timestamp
        )
        
        # Query similar locations from memory store
        similar = memory_store.query_memories(
            coordinates=(request.latitude, request.longitude),
            k=request.limit
        )
        
        # Calculate similarity scores
        results = []
        for mem in similar:
            # Calculate distance
            dist_km = np.sqrt(
                (mem["coordinates"][0] - request.latitude)**2 +
                (mem["coordinates"][1] - request.longitude)**2
            ) * 111  # Rough km conversion
            
            if dist_km <= request.radius_km:
                # Calculate feature similarity
                similarity = np.dot(
                    reference["embedding"].numpy().flatten(),
                    mem["embedding"].numpy().flatten()
                )
                
                results.append({
                    "coordinates": mem["coordinates"],
                    "distance_km": float(dist_km),
                    "similarity_score": float(similarity),
                    "metadata": mem["metadata"]
                })
        
        return {
            "status": "success",
            "reference_location": {
                "coordinates": (request.latitude, request.longitude),
                "metadata": reference["metadata"]
            },
            "similar_locations": sorted(
                results,
                key=lambda x: x["similarity_score"],
                reverse=True
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ContextRequest(BaseModel):
    """Request for location context."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: datetime
    context_window_days: int = Field(default=365)

@router.post("/get_context")
async def get_location_context(request: ContextRequest):
    """Get comprehensive context for a location."""
    try:
        # Get current state
        current = pipeline.process_location(
            coordinates=(request.latitude, request.longitude),
            timestamp=request.timestamp
        )
        
        # Get historical context
        start_time = request.timestamp - timedelta(days=request.context_window_days)
        historical = pipeline.process_time_series(
            coordinates=(request.latitude, request.longitude),
            time_range=(start_time, request.timestamp),
            interval_days=30
        )
        
        # Analyze trends
        trends = {}
        for source in data_sources:
            source_data = [
                result["metadata"].get(f"{source.name}_resolution")
                for result in historical
                if f"{source.name}_resolution" in result["metadata"]
            ]
            if source_data:
                trends[source.name] = {
                    "mean": float(np.mean(source_data)),
                    "std": float(np.std(source_data)),
                    "min": float(np.min(source_data)),
                    "max": float(np.max(source_data))
                }
        
        return {
            "status": "success",
            "current_state": {
                "timestamp": request.timestamp,
                "metadata": current["metadata"]
            },
            "historical_trends": trends,
            "temporal_context": {
                "window_days": request.context_window_days,
                "data_points": len(historical),
                "first_observation": historical[0]["metadata"]["timestamp"],
                "last_observation": historical[-1]["metadata"]["timestamp"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DecisionSupportRequest(BaseModel):
    """Request for decision support analysis."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    analysis_type: str = Field(..., description="Type of analysis to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict)

@router.post("/decision_support")
async def get_decision_support(request: DecisionSupportRequest):
    """Get decision support analysis for a location."""
    try:
        if request.analysis_type == "land_use_change":
            # Analyze land use changes and their implications
            return await analyze_land_use_impact(request)
        elif request.analysis_type == "climate_risk":
            # Assess climate-related risks
            return await analyze_climate_risk(request)
        elif request.analysis_type == "environmental_impact":
            # Evaluate environmental impact
            return await analyze_environmental_impact(request)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported analysis type: {request.analysis_type}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_land_use_impact(request: DecisionSupportRequest):
    """Analyze land use changes and their implications."""
    # Implementation specific to land use analysis
    pass

async def analyze_climate_risk(request: DecisionSupportRequest):
    """Assess climate-related risks for a location."""
    # Implementation specific to climate risk analysis
    pass

async def analyze_environmental_impact(request: DecisionSupportRequest):
    """Evaluate environmental impact of changes."""
    # Implementation specific to environmental impact analysis
    pass 