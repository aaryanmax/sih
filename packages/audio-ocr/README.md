# M3: Whisper & OCR Multi-Modal Processing

Handles audio transcription, word-level timestamp alignment, visual OCR text recognition on keyframes, and scene boundary frame sampling.

## Components
1. **Whisper Transcription**: Faster-Whisper / WhisperX for fast speech-to-text with timestamp intervals.
2. **Keyframe OCR**: PaddleOCR / EasyOCR for recognizing on-screen code, slide headings, text overlays, and labels.
3. **Adaptive Frame Sampler**: Uses PySceneDetect / OpenCV to extract candidate keyframes at scene transitions and uniform temporal steps.
