# Audio & OCR Multi-Modal Processing

Handles acoustic speech transcription, timestamp alignment, visual OCR text recognition on keyframes, and scene boundary frame sampling.

## Components

1. **Whisper Transcription (`whisper_processor.py`)**: Faster-Whisper interface for fast speech-to-text with timestamp intervals.
2. **Keyframe OCR (`ocr_processor.py`)**: PaddleOCR / EasyOCR for recognizing on-screen code, slide headings, text overlays, and labels.
3. **Adaptive Frame Sampler (`frame_sampler.py`)**: Uses PySceneDetect / OpenCV to extract candidate keyframes at scene transitions and uniform temporal steps.
