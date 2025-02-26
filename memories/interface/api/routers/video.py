from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
import aiofiles
import os
from datetime import datetime
import io

from ..core.config import VIDEO_DIR, MAX_VIDEO_SIZE, SUPPORTED_VIDEO_TYPES
from ..models.schemas import FileResponse, ErrorResponse

router = APIRouter(
    prefix="/video",
    tags=["video"],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)

def get_video_path(filename: str) -> str:
    """Generate a unique filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(VIDEO_DIR, f"{timestamp}_{filename}")

@router.post("", response_model=FileResponse)
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file
    """
    try:
        if file.content_type not in SUPPORTED_VIDEO_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported video type")
        
        content = await file.read()
        if len(content) > MAX_VIDEO_SIZE:
            raise HTTPException(status_code=413, detail="Video file too large")
        
        filepath = get_video_path(file.filename)
        
        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(content)
        
        return FileResponse(
            message="Video uploaded successfully",
            filename=os.path.basename(filepath),
            file_size=len(content),
            content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{filename}")
async def get_video(filename: str):
    """
    Retrieve video by filename
    """
    try:
        filepath = os.path.join(VIDEO_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Video not found")
        
        async with aiofiles.open(filepath, 'rb') as f:
            content = await f.read()
        
        # Determine content type based on file extension
        content_type = "video/mp4"  # default
        if filename.lower().endswith(".webm"):
            content_type = "video/webm"
        elif filename.lower().endswith(".mpeg"):
            content_type = "video/mpeg"
        elif filename.lower().endswith(".mov"):
            content_type = "video/quicktime"
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type=content_type,
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 