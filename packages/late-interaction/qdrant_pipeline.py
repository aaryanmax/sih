"""
Qdrant Multi-Vector Store Integration for Video Frames (M2 Module)
"""

import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models

class VideoVectorStore:
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = int(port or os.getenv("QDRANT_PORT", "6333"))
        self.collection_name = "sih_video_keyframes"
        try:
            self.client = QdrantClient(host=self.host, port=self.port, timeout=5.0)
        except Exception:
            self.client = None

    def initialize_schema(self, vector_dim: int = 128):
        """Creates collection with multivector support."""
        if not self.client:
            return
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=vector_dim,
                    distance=models.Distance.COSINE,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM
                    )
                )
            )
