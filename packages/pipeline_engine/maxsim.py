import numpy as np


def maxsim_score(query_embeddings: np.ndarray, doc_embeddings: np.ndarray) -> float:
    """
    Computes MaxSim score between query tokens and document patch embeddings.
    query_embeddings: [N_q, dim]
    doc_embeddings: [N_p, dim]
    """
    if query_embeddings.size == 0 or doc_embeddings.size == 0:
        return 0.0
    sims = np.dot(query_embeddings, doc_embeddings.T)
    return float(np.sum(np.max(sims, axis=1)))
