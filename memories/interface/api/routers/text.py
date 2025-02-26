from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import aiofiles
import os
from datetime import datetime

from ..core.config import TEXT_DIR, MAX_TEXT_SIZE
from ..models.schemas import TextUpload, TextResponse, ErrorResponse

router = APIRouter(
    prefix="/text",
    tags=["text"],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)

def get_text_path(filename: str) -> str:
    """Generate a unique filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(TEXT_DIR, f"{timestamp}_{filename}")

@router.post("", response_model=TextResponse)
async def upload_text(content: TextUpload):
    """
    Upload text content
    """
    try:
        if len(content.text.encode()) > MAX_TEXT_SIZE:
            raise HTTPException(status_code=413, detail="Text content too large")
        
        filename = f"text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = get_text_path(filename)
        
        async with aiofiles.open(filepath, 'w') as f:
            await f.write(content.text)
        
        return TextResponse(message="Text uploaded successfully", filename=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{filename}", response_model=TextUpload)
async def get_text(filename: str):
    """
    Retrieve text content by filename
    """
    try:
        filepath = os.path.join(TEXT_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Text file not found")
        
        async with aiofiles.open(filepath, 'r') as f:
            content = await f.read()
        return TextUpload(text=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 