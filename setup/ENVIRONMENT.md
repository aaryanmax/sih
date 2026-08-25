# ⚙️ Environment Configuration Reference

ChronoVision AI uses environment variables loaded from `.env` in the project root. Below is the complete configuration dictionary.

---

## 🔑 Environment Variables

### 1. Causal Explainability & Query Planning (Gemini)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | *(Required for live AI)* | Google AI Studio API key for scene reasoning & search query decomposition. |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Primary multimodal reasoning model. |
| `GEMINI_FALLBACK_MODEL` | `gemini-3.1-flash-lite` | Automatic circuit breaker fallback model if 3.5 experiences a timeout. |
| `EXPLAINABILITY_TIMEOUT_S` | `1.5` | Strict timeout in seconds before triggering fallback. |

---

### 2. Vector Database (Qdrant)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `QDRANT_HOST` | `localhost` (or `qdrant` in Docker) | Hostname for Qdrant service. |
| `QDRANT_PORT` | `6333` | REST port for Qdrant. |
| `QDRANT_COLLECTION` | `video_frames` | Default Qdrant collection storing ColQwen2 multi-vectors. |
| `QDRANT_VECTOR_NAME` | `colqwen` | Multi-vector field name configured for `MAX_SIM` comparisons. |
| `QDRANT_PATH` | `None` | Optional local disk path for embedded in-process Qdrant. |

---

### 3. Vision-Language Model Engine (vLLM)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `VLM_HOST` | `http://localhost:8001` | URL of the standalone Qwen2-VL inference server. |
| `MODEL_NAME` | `Qwen/Qwen2-VL-7B-Instruct` | Hugging Face repo ID for the visual reasoning engine. |
| `GPU_MEMORY_UTILIZATION` | `0.85` | Fraction of GPU VRAM reserved for vLLM context. |
| `MAX_MODEL_LEN` | `4096` | Maximum token sequence length for video prompts. |

---

### 4. Tri-Modal Hybrid Fusion Weights

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `WEIGHT_VISUAL` | `0.60` | Proportion of ranking score driven by ColPali visual patch MaxSim ($60\%$). |
| `WEIGHT_WHISPER` | `0.25` | Proportion of ranking score driven by Whisper speech transcript match ($25\%$). |
| `WEIGHT_OCR` | `0.15` | Proportion of ranking score driven by keyframe OCR overlay text ($15\%$). |

---

### 5. Web & API Server Settings

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `development` | Runtime environment (`development`, `production`, `test`). |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base URL used by the frontend to make API calls. |
| `APP_PORT` | `3000` (or `3001` in Docker) | Port for the Next.js frontend. |
| `API_PORT` | `8000` | Port for the FastAPI backend. |
