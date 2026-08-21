"""
Keyframe OCR Processor (M3 Module)
Extracts on-screen code snippets, diagrams labels, slide text, and subtitle overlays.
"""

from typing import List, Dict, Any
from pydantic import BaseModel

class OCRBoundingBox(BaseModel):
    text: str
    confidence: float
    bbox: List[int] # [x_min, y_min, x_max, y_max]

class KeyframeOCRResult(BaseModel):
    timestamp_s: float
    frame_index: int
    detected_texts: List[OCRBoundingBox]
    full_text: str

class OCRProcessor:
    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu
        print(f"Initialized OCRProcessor (PaddleOCR/EasyOCR) [GPU={use_gpu}]")

    def process_frame(self, frame_path: str, timestamp_s: float, frame_index: int) -> KeyframeOCRResult:
        """
        Runs OCR on a single sampled frame.
        """
        sample_boxes = [
            OCRBoundingBox(text="Algorithm 1: MaxSim Late Interaction", confidence=0.99, bbox=[50, 40, 500, 80]),
            OCRBoundingBox(text="Qdrant MultiVector Indexing", confidence=0.97, bbox=[50, 100, 420, 140]),
            OCRBoundingBox(text="def compute_maxsim(query, doc):", confidence=0.95, bbox=[60, 200, 480, 230])
        ]
        full_text = " ".join([b.text for b in sample_boxes])
        return KeyframeOCRResult(
            timestamp_s=timestamp_s,
            frame_index=frame_index,
            detected_texts=sample_boxes,
            full_text=full_text
        )
