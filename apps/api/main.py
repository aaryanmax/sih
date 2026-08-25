"""
FastAPI Main Application (M4 Module)
SIH Advanced Video Search Platform
"""

import os
import sys

_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, "..", ".."))
sys.path.insert(0, os.path.join(_project_root, "packages"))
sys.path.insert(0, os.path.join(_project_root, "apps", "api"))

import logging

# Suppress verbose HTTP request logs from httpx and huggingface
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

from fastapi import FastAPI, File, Form, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from routes.search import router as search_router

app = FastAPI(
    title="SIH Advanced Video Search API",
    description="Multimodal search engine with ColPali Late-Interaction & Qwen-VL",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)


@app.get("/health")
@app.get("/api/health")
async def health_check():
    qdrant_status = False
    collections_list = []
    try:
        from routes.search import _get_retriever

        retriever = _get_retriever()
        if retriever and retriever.client:
            cols = retriever.client.get_collections().collections
            collections_list = [c.name for c in cols]
            qdrant_status = True
    except Exception as exc:
        qdrant_status = False

    return {
        "status": "healthy" if qdrant_status else "degraded",
        "service": "ChronoVision AI Video Search Backend",
        "qdrant_connected": qdrant_status,
        "collections": collections_list,
        "engine": "ColPali Late-Interaction MaxSim",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
