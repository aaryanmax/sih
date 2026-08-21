"""
Late-Interaction MaxSim Scoring Engine (ColPali / ColBERT paradigm)
Computes fine-grained token-to-patch similarity alignments.
"""

import numpy as np
from typing import List, Dict, Any, Tuple

def compute_maxsim_score(query_embeddings: np.ndarray, doc_embeddings: np.ndarray) -> float:
    """
    Computes MaxSim score between Query Tokens (N_q, D) and Document/Frame Patches (N_d, D).
    
    Formula:
        Score = sum_{q in Query} max_{d in Doc} (cosine_sim(q, d))
    """
    # Normalize vectors
    q_norm = query_embeddings / (np.linalg.norm(query_embeddings, axis=-1, keepdims=True) + 1e-9)
    d_norm = doc_embeddings / (np.linalg.norm(doc_embeddings, axis=-1, keepdims=True) + 1e-9)
    
    # Cosine similarity matrix: (N_q, N_d)
    similarity_matrix = np.dot(q_norm, d_norm.T)
    
    # Maximum similarity per query token across all document patches
    max_sim_per_token = np.max(similarity_matrix, axis=1)
    
    # Late interaction aggregation
    total_score = float(np.sum(max_sim_per_token))
    return total_score

def get_token_patch_heatmap(query_tokens: List[str], query_embeddings: np.ndarray, doc_embeddings: np.ndarray) -> Dict[str, Any]:
    """
    Generates token-to-patch attention maps for UI visual explainability.
    """
    q_norm = query_embeddings / (np.linalg.norm(query_embeddings, axis=-1, keepdims=True) + 1e-9)
    d_norm = doc_embeddings / (np.linalg.norm(doc_embeddings, axis=-1, keepdims=True) + 1e-9)
    similarity_matrix = np.dot(q_norm, d_norm.T)
    
    alignments = []
    for idx, token in enumerate(query_tokens):
        best_patch_idx = int(np.argmax(similarity_matrix[idx]))
        score = float(similarity_matrix[idx, best_patch_idx])
        alignments.append({
            "token": token,
            "best_patch_index": best_patch_idx,
            "max_similarity": round(score, 4),
            "patch_distribution": similarity_matrix[idx].tolist()[:16] # First 16 patches sample
        })
        
    return {
        "overall_score": float(np.sum(np.max(similarity_matrix, axis=1))),
        "token_alignments": alignments
    }
