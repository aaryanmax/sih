"""
Patch Encoder for Late-Interaction Embeddings
Extracts token-level representations (multi-vectors) from VLM hidden states.
"""

from typing import List, Optional

import numpy as np
import torch


class PatchEncoder:
    def __init__(self, projection_dim: int = 128, hidden_dim: int = 4096, seed: int = 42):
        """
        Initialize the patch encoder.
        :param projection_dim: Target dimension for the multi-vector embeddings.
                               ColPali typically projects down to 128 dims for efficiency.
        :param hidden_dim: Hidden dimension of the VLM backbone (e.g. 4096 for Qwen2-VL).
        :param seed: Deterministic random seed for persistent projection weights.
        """
        self.projection_dim = projection_dim
        self.hidden_dim = hidden_dim

        # Initialize persistent deterministic projection matrix (or load ColPali linear layer)
        gen = torch.Generator().manual_seed(seed)
        weights = torch.randn((hidden_dim, projection_dim), generator=gen)
        self._projection_weights = weights / torch.norm(weights, dim=0, keepdim=True)

    def extract_patch_tokens(
        self, hidden_states: torch.Tensor, patch_mask: Optional[torch.Tensor] = None
    ) -> List[np.ndarray]:
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

        # Ensure projection matrix matches hidden dimension and device
        if hidden_dim != self._projection_weights.shape[0] or self._projection_weights.device != hidden_states.device:
            gen = torch.Generator(device="cpu").manual_seed(42)
            weights = torch.randn((hidden_dim, self.projection_dim), generator=gen).to(hidden_states.device)
            projection_weights = weights / torch.norm(weights, dim=0, keepdim=True)
        else:
            projection_weights = self._projection_weights.to(hidden_states.device)

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
