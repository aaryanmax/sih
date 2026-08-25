# Next.js Web Frontend for ChronoVision AI

Interactive user interface built with **Next.js 14**, **React 18**, **Node.js 24**, and **Tailwind CSS** for exploring video archives with late-interaction multi-vector search, token-to-patch attention heatmaps, causal explainability, and synchronized video playback.

## Features

- **Semantic Query Bar**: Natural language query input searching visual patch features, text overlays, and audio speech.
- **MaxSim Patch Heatmaps (`LateInteractionHeatmap.tsx`)**: Visualizes which image patches fired for each specific query token with a temporal sparkline scrubber.
- **Synchronized Video Player (`ReelPlayer.tsx`)**: Jumps immediately to the exact timestamp of the peak matching frame.
- **TikTok/Reels Feed (`/reels`)**: Vertical video feed optimized for short-form content exploration.
- **Multimodal Signal Breakdown**: Visualizes the blended score contributions across ColPali visual embeddings, Whisper transcripts, and OCR overlays.

## Running Locally

```bash
cd apps/web
npm install
npm run dev
```

For full environment deployment instructions, see [`setup/README.md`](../../setup/README.md).
