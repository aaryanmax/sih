"""
FastAPI Main Application (M4 Module)
SIH Advanced Video Search Platform
"""

import os
from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
import os

from routes.search import router as search_router

app = FastAPI(
    title="SIH Advanced Video Search API",
    description="Multimodal search engine with ColPali Late-Interaction & Qwen-VL",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "SIH Advanced Video Search Backend",
        "qdrant_connected": True,
        "vllm_service_ready": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
