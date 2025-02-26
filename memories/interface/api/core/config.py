import os
from pathlib import Path

# API Settings
API_V1_PREFIX = "/api/v1"
PROJECT_TITLE = "Memories API"
PROJECT_DESCRIPTION = "A lightweight and fast API for handling text, images, and videos"
VERSION = "1.0.0"

# Directory Settings
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
TEXT_DIR = os.path.join(UPLOAD_DIR, "text")
IMAGE_DIR = os.path.join(UPLOAD_DIR, "images")
VIDEO_DIR = os.path.join(UPLOAD_DIR, "videos")

# Create directories if they don't exist
for directory in [TEXT_DIR, IMAGE_DIR, VIDEO_DIR]:
    os.makedirs(directory, exist_ok=True)

# File size limits (in bytes)
MAX_TEXT_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB

# Supported file types
SUPPORTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
SUPPORTED_VIDEO_TYPES = ["video/mp4", "video/mpeg", "video/webm", "video/quicktime"] 