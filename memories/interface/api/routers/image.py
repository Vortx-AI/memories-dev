from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
import aiofiles
import os
from datetime import datetime
import io

from ..core.config import IMAGE_DIR, MAX_IMAGE_SIZE, SUPPORTED_IMAGE_TYPES
from ..models.schemas import FileResponse, ErrorResponse

router = APIRouter(
    prefix="/image",
    tags=["image"],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)

def get_image_path(filename: str) -> str:
    """Generate a unique filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(IMAGE_DIR, f"{timestamp}_{filename}")

@router.post("", response_model=FileResponse)
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image file
    """
    try:
        if file.content_type not in SUPPORTED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported image type")
        
        content = await file.read()
        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=413, detail="Image file too large")
        
        filepath = get_image_path(file.filename)
        
        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(content)
        
        return FileResponse(
            message="Image uploaded successfully",
            filename=os.path.basename(filepath),
            file_size=len(content),
            content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{filename}")
async def get_image(filename: str):
    """
    Retrieve image by filename
    """
    try:
        filepath = os.path.join(IMAGE_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Image not found")
        
        async with aiofiles.open(filepath, 'rb') as f:
            content = await f.read()
        
        # Determine content type based on file extension
        content_type = "image/jpeg"  # default
        if filename.lower().endswith(".png"):
            content_type = "image/png"
        elif filename.lower().endswith(".gif"):
            content_type = "image/gif"
        elif filename.lower().endswith(".webp"):
            content_type = "image/webp"
        
        return StreamingResponse(io.BytesIO(content), media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 