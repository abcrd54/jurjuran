import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.video import router as video_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Shopee Video Generator",
    description="Generate promotional videos from Shopee product links",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video_router)


@app.get("/")
async def root():
    return {
        "service": "Shopee Video Generator",
        "version": "2.0.0",
        "endpoints": {
            "POST /api/generate": "Generate video from Shopee URL",
            "GET /api/progress/{id}": "Check generation progress",
            "POST /api/batch": "Batch generate (max 5 URLs)",
            "GET /api/templates": "List available templates",
            "GET /api/aspect-ratios": "List aspect ratios",
            "GET /api/voices": "List TTS voices",
            "GET /api/health": "Health check",
            "GET /docs": "Swagger UI",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
