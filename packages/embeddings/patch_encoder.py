"""
Patch Encoder for Late-Interaction Embeddings
Extracts token-level representations (multi-vectors) from VLM hidden states.
"""

import torch
import numpy as np
from typing import List, Optional

class PatchEncoder:
    def __init__(self, projection_dim: int = 128):
        """
        Initialize the patch encoder.
        :param projection_dim: Target dimension for the multi-vector embeddings.
                               ColPali typically projects down to 128 dims for efficiency.
        """
        self.projection_dim = projection_dim

    def extract_patch_tokens(self, hidden_states: torch.Tensor, patch_mask: Optional[torch.Tensor] = None) -> List[np.ndarray]:
        """
        Extracts patch tokens from the last hidden state of a VLM.
        Crucial Implementation: DO NOT take the pooled output. We retain distinct vectors for each patch.
        
        :param hidden_states: Tensor of shape (Batch, Seq_Len, Hidden_Dim).
                              This represents the final hidden states from the VLM.
        :param patch_mask: Optional boolean mask indicating which tokens correspond to visual patches.
        :return: List of multi-vector embeddings, one per chunk/item in the batch.
                 Each is of shape (Num_Patches, Projection_Dim).
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape
        
        # A real implementation applies a learned linear projection here to reduce 
        # the hidden_dim (e.g., 4096) down to the projection_dim (e.g., 128) for efficient Qdrant storage.
        # Here we apply a simulated orthogonal projection for demonstration.
        
        # Simulated projection layer (in a real scenario, you load trained weights from ColPali)
        projection_weights = torch.randn((hidden_dim, self.projection_dim), device=hidden_states.device)
        projection_weights = projection_weights / torch.norm(projection_weights, dim=0, keepdim=True)
        
        # Project hidden states to embedding space: (Batch, Seq_Len, 128)
        projected_states = torch.matmul(hidden_states, projection_weights)
        
        # L2 normalize the projected states along the embedding dimension
        projected_states = torch.nn.functional.normalize(projected_states, p=2, dim=-1)
        
        multi_vectors = []
        for i in range(batch_size):
            if patch_mask is not None:
                # Filter out text/special tokens, keep only image patch tokens
                patches = projected_states[i][patch_mask[i]]
            else:
                # Assume all tokens are visual patches if no mask provided
                patches = projected_states[i]
                
            # Convert to numpy for downstream Qdrant insertion
            multi_vectors.append(patches.detach().cpu().numpy())
            
        return multi_vectors

if __name__ == "__main__":
    # Test script setup
    encoder = PatchEncoder(projection_dim=128)
    # Mock hidden states from VLM: 2 chunks, 128 patches each, 4096 hidden dim
    mock_hidden = torch.randn(2, 128, 4096)
    embeddings = encoder.extract_patch_tokens(mock_hidden)
    print(f"PatchEncoder initialized. Batch size processed: {len(embeddings)}")
    print(f"Shape of multi-vector output for first chunk: {embeddings[0].shape}")
