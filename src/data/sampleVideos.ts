import { VideoKeyframeMatch } from '../types';

export const sampleKeyframeMatches: VideoKeyframeMatch[] = [
  {
    id: 'match_1',
    videoId: 'sih_lecture_01',
    videoTitle: 'Lecture 14: ColPali Multi-Vector Late Interaction & Vision Transformers.mp4',
    timestampSeconds: 165.2,
    timestampFormatted: '02:45',
    score: 0.962,
    modality: 'visual_patches',
    category: 'Architecture Diagram',
    thumbnailPlaceholder: 'Architecture Diagram: Qwen2-VL Multi-Vector Projection',
    ocrExtractedText: 'Formula: Score(Q, D) = sum_{q in Q} max_{d in D} (cos_sim(q, d))\nQdrant MultiVectorConfig(comparator=MAX_SIM)',
    whisperTranscript: 'As you can see on this slide, the ColPali architecture preserves visual patch tokens instead of pooling them into a single vector.',
    qwenReasoning: 'Qwen2-VL identified an architectural diagram detailing the token-to-patch similarity matrix. Visual patch indices (3,2) and (4,5) contain the mathematical formula for MaxSim.',
    tokenScores: [
      { token: 'ColPali', bestPatch: 18, maxSim: 0.98 },
      { token: 'late', bestPatch: 26, maxSim: 0.94 },
      { token: 'interaction', bestPatch: 27, maxSim: 0.96 },
      { token: 'MaxSim', bestPatch: 35, maxSim: 0.99 },
      { token: 'formula', bestPatch: 36, maxSim: 0.92 }
    ],
    patchHeatmap: [
      0.1, 0.1, 0.2, 0.2, 0.1, 0.1, 0.1, 0.1,
      0.2, 0.3, 0.4, 0.5, 0.3, 0.2, 0.1, 0.1,
      0.2, 0.5, 0.95, 0.98, 0.6, 0.3, 0.2, 0.1,
      0.1, 0.4, 0.92, 0.99, 0.88, 0.4, 0.2, 0.1,
      0.1, 0.3, 0.85, 0.91, 0.76, 0.3, 0.1, 0.1,
      0.1, 0.2, 0.4, 0.6, 0.5, 0.2, 0.1, 0.1,
      0.1, 0.1, 0.2, 0.3, 0.2, 0.1, 0.1, 0.1,
      0.0, 0.1, 0.1, 0.1, 0.1, 0.0, 0.0, 0.0
    ],
    timelineHeatmap: Array.from({length: 40}, (_, i) => {
      const ts = i * 15; // 15 sec chunks for 10 min video
      let score = Math.random() * 0.1 + 0.05;
      if (Math.abs(ts - 165.2) < 20) score = 0.962;
      else if (Math.abs(ts - 165.2) < 40) score = 0.6;
      else if (ts === 300) score = 0.4;
      return { timestamp: ts, score };
    })
  },
  {
    id: 'match_2',
    videoId: 'sih_tutorial_02',
    videoTitle: 'Workshop: Fast Multimodal Ingestion with PaddleOCR & WhisperX.mp4',
    timestampSeconds: 438.0,
    timestampFormatted: '07:18',
    score: 0.914,
    modality: 'ocr_text',
    category: 'Code Implementation',
    thumbnailPlaceholder: 'Code Editor: Python Qdrant Client Setup',
    ocrExtractedText: 'client.create_collection(\n  collection_name="sih_video_keyframes",\n  vectors_config=models.VectorParams(\n    size=128,\n    distance=models.Distance.COSINE,\n    multivector_config=models.MultiVectorConfig(comparator=models.MultiVectorComparator.MAX_SIM)\n  )\n)',
    whisperTranscript: 'Now we define the Qdrant schema with the multi-vector comparator set to MaxSim so late interaction runs natively in the database.',
    qwenReasoning: 'Qwen2-VL spotted a VS Code screen displaying Python code creating a Qdrant multivector collection with dimension 128.',
    tokenScores: [
      { token: 'Qdrant', bestPatch: 12, maxSim: 0.95 },
      { token: 'multivector', bestPatch: 20, maxSim: 0.93 },
      { token: 'indexing', bestPatch: 28, maxSim: 0.89 },
      { token: 'setup', bestPatch: 36, maxSim: 0.88 }
    ],
    patchHeatmap: [
      0.3, 0.4, 0.4, 0.3, 0.1, 0.1, 0.1, 0.1,
      0.5, 0.85, 0.92, 0.88, 0.2, 0.1, 0.1, 0.1,
      0.4, 0.91, 0.96, 0.90, 0.3, 0.2, 0.1, 0.1,
      0.3, 0.88, 0.94, 0.85, 0.2, 0.1, 0.1, 0.1,
      0.2, 0.75, 0.80, 0.70, 0.1, 0.1, 0.1, 0.0,
      0.1, 0.2, 0.3, 0.2, 0.1, 0.1, 0.0, 0.0,
      0.1, 0.1, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0,
      0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    ],
    timelineHeatmap: Array.from({length: 40}, (_, i) => {
      const ts = i * 15;
      let score = Math.random() * 0.1 + 0.05;
      if (Math.abs(ts - 438.0) < 20) score = 0.914;
      else if (Math.abs(ts - 438.0) < 40) score = 0.5;
      return { timestamp: ts, score };
    })
  },
  {
    id: 'match_3',
    videoId: 'sih_demo_03',
    videoTitle: 'Live Demo: Autonomous Drone Surveillance & Object Detection.mp4',
    timestampSeconds: 52.4,
    timestampFormatted: '00:52',
    score: 0.882,
    modality: 'visual_patches',
    category: 'Real-world Camera',
    thumbnailPlaceholder: 'Drone Camera: Autonomous Vehicle Tracking with BBoxes',
    ocrExtractedText: 'CAMERA_ID: DRONE_ALPHA_09 | GPS: 28.6139° N, 77.2090° E | ALT: 42m',
    whisperTranscript: 'Target vehicle identified near intersection B-4. High confidence visual tracking active.',
    qwenReasoning: 'Qwen2-VL localized a silver sedan in the central visual quadrant with tracking telemetry on the upper boundary.',
    tokenScores: [
      { token: 'autonomous', bestPatch: 34, maxSim: 0.89 },
      { token: 'vehicle', bestPatch: 35, maxSim: 0.96 },
      { token: 'detection', bestPatch: 43, maxSim: 0.91 }
    ],
    patchHeatmap: [
      0.1, 0.1, 0.1, 0.2, 0.2, 0.1, 0.1, 0.1,
      0.1, 0.2, 0.3, 0.4, 0.4, 0.3, 0.2, 0.1,
      0.1, 0.3, 0.6, 0.8, 0.82, 0.6, 0.3, 0.1,
      0.2, 0.4, 0.85, 0.98, 0.95, 0.8, 0.4, 0.2,
      0.2, 0.3, 0.75, 0.92, 0.89, 0.7, 0.3, 0.1,
      0.1, 0.2, 0.4, 0.5, 0.5, 0.3, 0.2, 0.1,
      0.1, 0.1, 0.2, 0.2, 0.2, 0.1, 0.1, 0.1,
      0.0, 0.0, 0.1, 0.1, 0.1, 0.0, 0.0, 0.0
    ],
    timelineHeatmap: Array.from({length: 40}, (_, i) => {
      const ts = i * 15;
      let score = Math.random() * 0.1 + 0.05;
      if (Math.abs(ts - 52.4) < 15) score = 0.882;
      return { timestamp: ts, score };
    })
  },
  {
    id: 'match_4',
    videoId: 'sih_lecture_01',
    videoTitle: 'Lecture 14: ColPali Multi-Vector Late Interaction & Vision Transformers.mp4',
    timestampSeconds: 580.0,
    timestampFormatted: '09:40',
    score: 0.851,
    modality: 'speech_audio',
    category: 'Spoken Concept',
    thumbnailPlaceholder: 'Speaker Presentation: Latency and VRAM Benchmarks',
    ocrExtractedText: 'Comparison: CLIP Single Vector vs ColPali Multi-Vector\nRetrieval Recall@1: 58.2% -> 87.6%',
    whisperTranscript: 'The trade-off is slightly higher index storage, but recall jumps from 58% to nearly 88% on complex visual queries.',
    qwenReasoning: 'Qwen2-VL parsed a benchmark comparison bar chart demonstrating Recall@1 accuracy gains with ColPali.',
    tokenScores: [
      { token: 'recall', bestPatch: 42, maxSim: 0.91 },
      { token: 'benchmark', bestPatch: 43, maxSim: 0.87 },
      { token: 'comparison', bestPatch: 50, maxSim: 0.85 }
    ],
    patchHeatmap: [
      0.1, 0.2, 0.2, 0.2, 0.1, 0.1, 0.1, 0.1,
      0.2, 0.4, 0.5, 0.5, 0.3, 0.2, 0.1, 0.1,
      0.2, 0.6, 0.88, 0.82, 0.7, 0.4, 0.2, 0.1,
      0.2, 0.7, 0.94, 0.90, 0.82, 0.5, 0.3, 0.1,
      0.1, 0.5, 0.80, 0.85, 0.75, 0.4, 0.2, 0.1,
      0.1, 0.3, 0.4, 0.5, 0.4, 0.2, 0.1, 0.1,
      0.1, 0.1, 0.2, 0.2, 0.2, 0.1, 0.1, 0.0,
      0.0, 0.0, 0.1, 0.1, 0.1, 0.0, 0.0, 0.0
    ],
    timelineHeatmap: Array.from({length: 40}, (_, i) => {
      const ts = i * 15;
      let score = Math.random() * 0.1 + 0.05;
      if (Math.abs(ts - 89.0) < 15) score = 0.841;
      return { timestamp: ts, score };
    })
  }
];
