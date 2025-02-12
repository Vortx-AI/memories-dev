from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path

from ..core.memory import EarthMemoryStore
from ..core.synthesis import SynthesisPipeline, SatelliteDataSource

router = APIRouter(prefix="/memory", tags=["memory"])

# Initialize services
memory_store = EarthMemoryStore(Path("/app/data/memories"))

# Configure data sources
satellite_source = SatelliteDataSource(
    name="sentinel2",
    resolution=10.0,
    bands=["B02", "B03", "B04", "B08"],  # RGB + NIR
    data_path=Path("/app/data/satellite")
)

pipeline = SynthesisPipeline(
    data_sources=[satellite_source],
    memory_store=memory_store
)

class MemoryQuery(BaseModel):
    """Query parameters for memory retrieval."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=5, ge=1, le=100)

class MemoryResponse(BaseModel):
    """Response model for memory queries."""
    coordinates: tuple
    timestamp: datetime
    metadata: Dict[str, Any]
    embedding: List[float]

@router.post("/query", response_model=List[MemoryResponse])
async def query_memories(query: MemoryQuery):
    """Query memories by location and time range."""
    try:
        time_range = None
        if query.start_time and query.end_time:
            time_range = (query.start_time, query.end_time)
            
        memories = memory_store.query_memories(
            coordinates=(query.latitude, query.longitude),
            time_range=time_range,
            k=query.limit
        )
        
        return [
            MemoryResponse(
                coordinates=mem["coordinates"],
                timestamp=mem["timestamp"],
                metadata=mem["metadata"],
                embedding=mem["embedding"].tolist()
            )
            for mem in memories
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ProcessRequest(BaseModel):
    """Request model for processing new locations."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

@router.post("/process")
async def process_location(request: ProcessRequest):
    """Process a new location and store it in memory."""
    try:
        result = pipeline.process_location(
            coordinates=(request.latitude, request.longitude),
            timestamp=request.timestamp,
            metadata=request.metadata
        )
        
        return {
            "status": "success",
            "embedding": result["embedding"].tolist(),
            "metadata": result["metadata"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TimeSeriesRequest(BaseModel):
    """Request model for processing time series data."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    start_time: datetime
    end_time: datetime
    interval_days: int = Field(default=1, ge=1)

@router.post("/process_time_series")
async def process_time_series(request: TimeSeriesRequest):
    """Process a location across a time range."""
    try:
        results = pipeline.process_time_series(
            coordinates=(request.latitude, request.longitude),
            time_range=(request.start_time, request.end_time),
            interval_days=request.interval_days
        )
        
        return {
            "status": "success",
            "count": len(results),
            "results": [
                {
                    "timestamp": result["metadata"]["timestamp"],
                    "embedding": result["embedding"].tolist(),
                    "metadata": result["metadata"]
                }
                for result in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Check the health of the memory service."""
    return {
        "status": "healthy",
        "memory_count": len(memory_store.memory_index)
    } 