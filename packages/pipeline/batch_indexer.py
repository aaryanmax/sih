"""
Batch Ingestion Orchestrator (Phase 1)
Master pipeline that processes .mp4 files, extracts multimodal features (VLM multi-vectors, Whisper audio, OCR),
and commits them into Qdrant for Late-Interaction MaxSim search.
"""

import os
import sys
import glob
import uuid
import torch
import logging
from typing import List

# Setup paths to import from hyphenated directories
current_dir = os.path.dirname(__file__)
packages_dir = os.path.abspath(os.path.join(current_dir, '..'))

sys.path.append(os.path.join(packages_dir, 'vlm-engine'))
sys.path.append(os.path.join(packages_dir, 'embeddings'))
sys.path.append(os.path.join(packages_dir, 'audio-ocr'))

from video_chunker import VideoChunker
from patch_encoder import PatchEncoder
from maxsim_scorer import MaxSimRetriever
from whisper_processor import WhisperAudioProcessor
from ocr_processor import OCRProcessor
from qdrant_client.http import models

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BatchIndexer")

class BatchIndexer:
    def __init__(self, video_dir: str = "./data/raw_videos"):
        self.video_dir = video_dir
        self.chunk_duration_sec = 2.0
        self.fps_target = 2.0
        
        logger.info("Initializing Batch Ingestion Orchestrator...")
        
        # 1. Initialize core components
        self.chunker = VideoChunker(fps_target=self.fps_target, chunk_duration_sec=self.chunk_duration_sec)
        self.patch_encoder = PatchEncoder(projection_dim=128)
        self.qdrant_retriever = MaxSimRetriever(collection_name="sih_video_keyframes")
        
        # Audio and OCR modules
        self.whisper = WhisperAudioProcessor(model_size="base")
        self.ocr = OCRProcessor()
        
        # Ensure Qdrant MultiVector schema is ready
        self.qdrant_retriever.initialize_schema(vector_dim=128)

    def _get_transcript_for_window(self, segments, start_time: float, end_time: float) -> str:
        """Finds audio transcript text overlapping with the temporal window."""
        overlapping = []
        for seg in segments:
            # Check for temporal overlap
            if seg.start_s < end_time and seg.end_s > start_time:
                overlapping.append(seg.text)
        return " ".join(overlapping).strip()

    def _extract_vlm_hidden_states(self, chunk) -> torch.Tensor:
        """
        Interacts with the vLLM inference server to extract hidden states from the chunk.
        In a production deployment, this makes an HTTP request to http://vlm-engine:8001/internal/extract_embeddings
        or calls the loaded engine locally.
        
        Returns: Tensor of shape (Batch, Num_Patches, Hidden_Dim) e.g., (1, 128, 4096)
        """
        # Simulated hidden states output for architectural completeness
        # Assume Qwen2-VL-7B uses a hidden dimension of 4096 and we extract 128 patches
        return torch.randn(1, 128, 4096)

    def process_directory(self):
        """Scans the input video directory and iterates over each video."""
        if not os.path.exists(self.video_dir):
            logger.error(f"Directory {self.video_dir} does not exist.")
            return

        video_files = glob.glob(os.path.join(self.video_dir, "*.mp4"))
        if not video_files:
            logger.warning(f"No .mp4 files found in {self.video_dir}")
            return

        for video_path in video_files:
            try:
                self.process_video(video_path)
            except Exception as e:
                logger.error(f"Failed to process video {video_path}: {e}")

    def process_video(self, video_path: str):
        """Processes a single video end-to-end and ingests it into Qdrant."""
        video_filename = os.path.basename(video_path)
        video_id = str(uuid.uuid5(uuid.NAMESPACE_URL, video_filename))
        logger.info(f"Processing video: {video_filename} (ID: {video_id})")

        # 2. Extract chronological 2-second chunks using VideoChunker
        chunks = self.chunker.process(video_path)
        logger.info(f"Extracted {len(chunks)} chronological chunks.")

        # 3. Extract Whisper transcript segments (word-level/segment-level timestamps)
        transcript_segments = self.whisper.transcribe_video_audio(video_path)

        points_to_insert = []
        
        for idx, chunk in enumerate(chunks):
            start_time = idx * self.chunk_duration_sec
            end_time = start_time + self.chunk_duration_sec
            
            # 4. Send chunks to inference_server to get hidden states
            hidden_states = self._extract_vlm_hidden_states(chunk)
            
            # 5. Send hidden states to patch_encoder to get L2-normalized patch-level multi-vectors
            # multi_vectors_batch is a list of (Num_Patches, Projection_Dim) arrays
            multi_vectors_batch = self.patch_encoder.extract_patch_tokens(hidden_states)
            chunk_multi_vector = multi_vectors_batch[0]
            
            # 6. Extract OCR for the current window 
            # (In production, write the chunk's center frame to disk or pass tensor directly)
            ocr_result = self.ocr.process_frame("dummy_frame_path.jpg", timestamp_s=start_time, frame_index=idx)
            
            # 7. Match synchronized audio transcript to this 2-second window
            window_transcript = self._get_transcript_for_window(transcript_segments, start_time, end_time)

            # 8. Package chunk into a single Qdrant point
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{video_id}_{idx}"))
            
            payload = {
                "video_id": video_id,
                "video_filename": video_filename,
                "start_time": start_time,
                "end_time": end_time,
                "transcript_text": window_transcript,
                "ocr_text": ocr_result.full_text,
                "keyframe_url": f"/assets/frames/{video_id}/frame_{idx:04d}.jpg"
            }

            # Qdrant expects a list of lists for MultiVector payloads
            vector_payload = chunk_multi_vector.tolist()

            point = models.PointStruct(
                id=point_id,
                vector=vector_payload,
                payload=payload
            )
            points_to_insert.append(point)

        # 9. Batch insert points into Qdrant for fast ingestion
        if points_to_insert:
            logger.info(f"Batch inserting {len(points_to_insert)} multi-vector points into Qdrant...")
            self.qdrant_retriever.insert_multi_vectors(points_to_insert)
            logger.info(f"Successfully ingested {video_filename} into Qdrant.")

if __name__ == "__main__":
    indexer = BatchIndexer()
    
    # Create target directories if they don't exist
    os.makedirs("./data/raw_videos", exist_ok=True)
    os.makedirs("./data/extracted_frames", exist_ok=True)
    
    # Run the orchestrator
    indexer.process_directory()
