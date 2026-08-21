export interface MonorepoNode {
  id: string;
  name: string;
  type: 'folder' | 'file';
  path: string;
  milestone?: string;
  description?: string;
  content?: string;
  language?: string;
  children?: MonorepoNode[];
}

export interface TimelinePoint {
  timestamp: number;
  score: number;
}

export interface VideoKeyframeMatch {
  id: string;
  videoId: string;
  videoTitle: string;
  timestampSeconds: number;
  timestampFormatted: string;
  score: number;
  modality: 'visual_patches' | 'speech_audio' | 'ocr_text';
  category: string;
  thumbnailPlaceholder: string;
  ocrExtractedText: string;
  whisperTranscript: string;
  qwenReasoning: string;
  tokenScores: { token: string; bestPatch: number; maxSim: number }[];
  patchHeatmap: number[]; // 64 values (8x8 grid) between 0 and 1
  timelineHeatmap?: TimelinePoint[];
}

export interface ArchitectureModule {
  id: string;
  code: 'M1' | 'M2' | 'M3' | 'M4' | 'M5' | 'M6';
  name: string;
  path: string;
  techStack: string[];
  role: string;
  keyFiles: string[];
  inputs: string;
  outputs: string;
  status: 'Ready' | 'Configured';
}
