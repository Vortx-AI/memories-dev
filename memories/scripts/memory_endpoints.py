"""
FastAPI endpoints for Earth memory operations.
"""

from fastapi import FastAPI, HTTPException, File, UploadFile
from typing import Dict, List, Optional
from pydantic import BaseModel
import mercantile
from datetime import datetime
import os
from dotenv import load_dotenv
from memories.utils.types import Bounds
from memories.utils.privacy.secure_encoding import SecureImageEncoder, SecureAPILayer
from memories.synthetic.generator import SyntheticDataGenerator
from memories.core.memory_manager import MemoryManager

# Load environment variables
load_dotenv()

app = FastAPI(title="Earth Memories API")

# Initialize components with secure key from environment
master_key = os.getenv('MEMORIES_MASTER_KEY')
if not master_key:
    raise ValueError("MEMORIES_MASTER_KEY environment variable is required")
secure_layer = SecureAPILayer(master_key=master_key)
synthetic_generator = SyntheticDataGenerator()
memory_manager = MemoryManager()

class MemoryRequest(BaseModel):
    """Memory request model"""
    bounds: Dict[str, float]
    timestamp: Optional[str] = None
    protection_level: Optional[str] = 'high'
    metadata: Optional[Dict] = {}

class MemoryResponse(BaseModel):
    """Memory response model"""
    memory_id: str
    bounds: Dict[str, float]
    timestamp: str
    access_token: str
    metadata: Dict

@app.post("/memories/store")
async def store_memory(
    request: MemoryRequest,
    image: UploadFile = File(...)
):
    """Store a new Earth memory"""
    try:
        # Convert bounds
        bounds = mercantile.LngLatBbox(
            west=request.bounds['west'],
            south=request.bounds['south'],
            east=request.bounds['east'],
            north=request.bounds['north']
        )
        
        # Read image data
        image_data = await image.read()
        
        # Encode and store
        encrypted_data, secure_metadata = secure_layer.encode_tile(
            image_data,
            request.metadata,
            request.protection_level
        )
        
        # Store encrypted data in memory manager
        memory_manager.store(
            data_id=secure_metadata['id'],
            data=encrypted_data,
            metadata=secure_metadata,
            tier='hot'  # Store in hot tier for fast access
        )
        
        # Generate response
        response = MemoryResponse(
            memory_id=secure_metadata['id'],
            bounds=request.bounds,
            timestamp=datetime.utcnow().isoformat(),
            access_token=secure_metadata['access_token'],
            metadata=secure_metadata
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memories/{memory_id}")
async def get_memory(
    memory_id: str,
    access_token: str
):
    """Retrieve an Earth memory"""
    try:
        # Retrieve from memory manager
        memory_data = memory_manager.retrieve(memory_id)
        if not memory_data:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        encrypted_data = memory_data.get('data')
        secure_metadata = memory_data.get('metadata')
        
        decoded_data = secure_layer.decode_tile(
            encrypted_data,
            secure_metadata,
            access_token
        )
        
        if decoded_data is None:
            raise HTTPException(status_code=403, detail="Access denied")
            
        return decoded_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memories/synthetic")
async def generate_synthetic(request: MemoryRequest):
    """Generate synthetic Earth memory"""
    try:
        # Convert bounds
        bounds = mercantile.LngLatBbox(
            west=request.bounds['west'],
            south=request.bounds['south'],
            east=request.bounds['east'],
            north=request.bounds['north']
        )
        
        # Generate synthetic data
        synthetic_data = synthetic_generator.generate_multispectral(bounds)
        
        # Encode and secure
        encrypted_data, secure_metadata = secure_layer.encode_tile(
            synthetic_data,
            request.metadata,
            request.protection_level
        )
        
        # Generate response
        response = MemoryResponse(
            memory_id=secure_metadata['id'],
            bounds=request.bounds,
            timestamp=datetime.utcnow().isoformat(),
            access_token=secure_metadata['access_token'],
            metadata=secure_metadata
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    access_token: str
):
    """Delete an Earth memory"""
    try:
        # Verify access
        if not secure_layer.validate_api_key(access_token, 'delete'):
            raise HTTPException(status_code=403, detail="Access denied")
            
        # Delete from memory manager
        success = memory_manager.delete(memory_id)
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {"status": "success", "message": "Memory deleted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 