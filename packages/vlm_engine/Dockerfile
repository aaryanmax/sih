# Production Dockerfile for Qwen-VL Inference Engine Server
FROM python:3.14-slim

WORKDIR /app

# Install system dependencies & ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY packages/vlm_engine/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY packages/vlm_engine /app/packages/vlm_engine

ENV PYTHONPATH=/app/packages/vlm_engine:$PYTHONPATH
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 0

CMD ["python", "-m", "uvicorn", "inference_server:app", "--host", "0.0.0.0", "--port", "8001"]
