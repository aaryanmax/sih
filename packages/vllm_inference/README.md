# vLLM Inference Engine for Qwen-VL

Provides low-latency, high-throughput multimodal vision-language model serving via the vLLM engine for Qwen2-VL.

## Architecture

- **Model**: `Qwen/Qwen2-VL-7B-Instruct` (Vision + Text)
- **Engine**: vLLM OpenAI-Compatible Server
- **Capabilities**:
  - Fine-grained visual question answering on extracted video frames
  - Temporal scene narration and dense captioning
  - Multi-frame video comprehension

## Quick Start

```bash
pip install -r requirements.txt
python -m packages.vllm_inference.inference_service --model Qwen/Qwen2-VL-7B-Instruct
```
