from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import API_V1_PREFIX, PROJECT_TITLE, PROJECT_DESCRIPTION, VERSION
from .routers import text, image, video, memory

# Create FastAPI app
app = FastAPI(
    title=PROJECT_TITLE,
    description=PROJECT_DESCRIPTION,
    version=VERSION,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(text.router, prefix=API_V1_PREFIX)
app.include_router(image.router, prefix=API_V1_PREFIX)
app.include_router(video.router, prefix=API_V1_PREFIX)
app.include_router(memory.router, prefix=API_V1_PREFIX)

@app.get("/")
async def root():
    """
    Root endpoint - provides API information
    """
    return {
        "title": PROJECT_TITLE,
        "version": VERSION,
        "description": PROJECT_DESCRIPTION,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 