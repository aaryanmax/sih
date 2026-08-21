"""
Video Chunker for VLM Engine
Reads raw .mp4 files and intelligently slices them into processable chunks.
"""

import os
import torch
import decord
from decord import VideoReader, cpu

# Configure decord to output PyTorch tensors natively for zero-copy speed
decord.bridge.set_bridge('torch')

class VideoChunker:
    def __init__(self, fps_target: float = 2.0, chunk_duration_sec: float = 2.0):
        """
        Initialize the video chunker.
        :param fps_target: Frames per second to extract.
        :param chunk_duration_sec: Duration of each chunk in seconds.
        """
        self.fps_target = fps_target
        self.chunk_duration_sec = chunk_duration_sec
        self.frames_per_chunk = int(fps_target * chunk_duration_sec)

    def process_video(self, video_path: str) -> torch.Tensor:
        """
        Uses a sliding window approach to extract chunks.
        Returns a chronologically structured tensor of frames so M-RoPE understands time.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Use decord for fast, direct-to-tensor video decoding
        vr = VideoReader(video_path, ctx=cpu(0))
        native_fps = vr.get_avg_fps()
        total_frames = len(vr)
        
        if native_fps == 0 or total_frames == 0:
            raise ValueError("Invalid video file or no frames found.")

        # Calculate frame indices for target FPS
        frame_interval = native_fps / self.fps_target
        target_frame_indices = [int(i * frame_interval) for i in range(int(total_frames / frame_interval))]
        
        # Ensure we don't exceed actual frame count
        target_frame_indices = [idx for idx in target_frame_indices if idx < total_frames]

        # Extract frames: Shape is (N, H, W, C)
        frames = vr.get_batch(target_frame_indices)

        # PyTorch models expect (N, C, H, W)
        frames = frames.permute(0, 3, 1, 2)

        # Group into chunks: (Num_Chunks, Frames_per_Chunk, C, H, W)
        num_complete_chunks = len(frames) // self.frames_per_chunk
        
        if num_complete_chunks > 0:
            # Truncate trailing frames that don't make a full chunk for simplicity
            chunked_tensors = frames[:num_complete_chunks * self.frames_per_chunk]
            chunked_tensors = chunked_tensors.view(
                num_complete_chunks, 
                self.frames_per_chunk, 
                frames.shape[1], 
                frames.shape[2], 
                frames.shape[3]
            )
        else:
            # Fallback if video is too short
            chunked_tensors = torch.empty((0, self.frames_per_chunk, frames.shape[1], frames.shape[2], frames.shape[3]))

        return chunked_tensors

if __name__ == "__main__":
    print("VideoChunker initialized. Ready to process .mp4 files.")
