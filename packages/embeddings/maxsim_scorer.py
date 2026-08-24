"""
Late-Interaction MaxSim Retrieval (M2)
Handles schema initialization for multivector payloads in Qdrant and executes MaxSim scoring.
"""

import os
from typing import Any, Dict, List

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models


class MaxSimRetriever:
    def __init__(self, collection_name: str = "sih_video_keyframes"):
        self.collection_name = collection_name

        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

        try:
            self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
            print(f"MaxSimRetriever connected to Qdrant at {qdrant_host}:{qdrant_port}")
        except Exception as e:
            print(f"Warning: Could not connect to Qdrant: {e}")
            self.client = None

    def initialize_schema(self, vector_dim: int = 128):
        """
        Initializes the Qdrant schema to explicitly accept multivector payloads
        configured for Late-Interaction MaxSim search.
        """
        if not self.client:
            print("Qdrant client not available. Skipping schema init.")
            return

        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            print(f"Creating Qdrant collection '{self.collection_name}' with MultiVectorConfig(MAX_SIM)...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=vector_dim,
                    distance=models.Distance.COSINE,
                    # Crucial implementation strategy: Qdrant handles MaxSim natively
                    multivector_config=models.MultiVectorConfig(comparator=models.MultiVectorComparator.MAX_SIM),
                ),
            )
            print("Schema initialized successfully.")
        else:
            print(f"Collection '{self.collection_name}' already exists.")

    def insert_multi_vectors(self, points: List[models.PointStruct]):
        """
        Inserts multivector points (visual patch tokens) into Qdrant.
        """
        if self.client:
            self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, query_multi_vector: np.ndarray, top_k: int = 10) -> List[Any]:
        """
        Executes a Late-Interaction MaxSim search against the stored patch tokens.

        :param query_multi_vector: Embedded query text tokens (Num_Tokens, Projection_Dim)
        :param top_k: Number of results to return
        :return: Ranked list of search results
        """
        if not self.client:
            return []

        # Convert numpy array (Num_Tokens, Dim) to a list of lists for Qdrant payload
        query_list = query_multi_vector.tolist()

        search_result = self.client.search(
            collection_name=self.collection_name, query_vector=query_list, limit=top_k, with_payload=True
        )
        return search_result


if __name__ == "__main__":
    retriever = MaxSimRetriever()
    # Assuming standard ColPali 128 dimension projection
    retriever.initialize_schema(vector_dim=128)
