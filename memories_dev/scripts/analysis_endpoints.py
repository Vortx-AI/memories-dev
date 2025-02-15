"""
FastAPI endpoints for Earth observation data analysis.
"""

from fastapi import FastAPI, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel
import mercantile
from ..utils.types import Bounds
from .advanced_analysis import AdvancedAnalysis

app = FastAPI(title="Earth Observation Analysis API")
analyzer = AdvancedAnalysis()

class AnalysisRequest(BaseModel):
    """Analysis request model"""
    bounds: Dict[str, float]  # west, south, east, north
    analyses: Optional[List[str]] = ['vegetation', 'urban', 'change']
    time_range: Optional[str] = None

class VegetationRequest(BaseModel):
    """Vegetation analysis request model"""
    bounds: Dict[str, float]
    time_range: Optional[str] = None

class UrbanRequest(BaseModel):
    """Urban analysis request model"""
    bounds: Dict[str, float]
    layers: Optional[List[str]] = ['buildings', 'roads']

class ChangeRequest(BaseModel):
    """Change analysis request model"""
    bounds: Dict[str, float]
    start_time: str
    end_time: str

@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    """Generate comprehensive analysis report"""
    try:
        bounds = mercantile.LngLatBbox(
            west=request.bounds['west'],
            south=request.bounds['south'],
            east=request.bounds['east'],
            north=request.bounds['north']
        )
        
        report = analyzer.generate_report(
            bounds=bounds,
            analyses=request.analyses
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/vegetation")
async def analyze_vegetation(request: VegetationRequest):
    """Analyze vegetation indices"""
    try:
        bounds = mercantile.LngLatBbox(
            west=request.bounds['west'],
            south=request.bounds['south'],
            east=request.bounds['east'],
            north=request.bounds['north']
        )
        
        results = analyzer.analyze_vegetation(
            bounds=bounds,
            time_range=request.time_range
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/urban")
async def analyze_urban(request: UrbanRequest):
    """Analyze urban patterns"""
    try:
        bounds = mercantile.LngLatBbox(
            west=request.bounds['west'],
            south=request.bounds['south'],
            east=request.bounds['east'],
            north=request.bounds['north']
        )
        
        results = analyzer.analyze_urban_patterns(
            bounds=bounds,
            layers=request.layers
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/change")
async def analyze_change(request: ChangeRequest):
    """Analyze changes between time periods"""
    try:
        bounds = mercantile.LngLatBbox(
            west=request.bounds['west'],
            south=request.bounds['south'],
            east=request.bounds['east'],
            north=request.bounds['north']
        )
        
        results = analyzer.analyze_change(
            bounds=bounds,
            start_time=request.start_time,
            end_time=request.end_time
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 