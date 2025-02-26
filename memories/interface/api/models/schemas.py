from pydantic import BaseModel, Field
from typing import Optional

class TextUpload(BaseModel):
    text: str = Field(..., description="Text content to upload")

class TextResponse(BaseModel):
    message: str
    filename: str

class FileResponse(BaseModel):
    message: str
    filename: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None

class ErrorResponse(BaseModel):
    detail: str 