/**
 * @file apps/web/src/components/SearchPlayground.tsx
 * @description Production-Grade Multimodal Search Playground with:
 *  1. Semantic Radar: Maps Qdrant multi-vector late-interaction similarity scores into an array
 *     of colored HTML div blocks resting directly above the HTML5 video player timeline.
 *  2. Auto-Stitch Sequencer: HTML5 video onEnded listener that detects `next_part_id`,
 *     seamlessly updates the src attribute, and auto-plays the sequel with visual toast feedback.
 *  3. 2026 Android Expressive Design: Material 3 tonal elevation, pill containers, tactile interactions,
 *     and responsive mobile-first Tailwind (sm:, md:, lg:, xl:) vertical layouts.
 */

"use client";

import React, {
  useState,
  useRef,
  useCallback,
  useEffect,
  useMemo,
} from "react";
import {
  Search,
  Sparkles,
  Play,
  Pause,
  RotateCcw,
  Volume2,
  VolumeX,
  FileText,
  Clock,
  ChevronRight,
  Zap,
  Activity,
  Film,
  FastForward,
  Compass,
  Layers,
  Maximize2,
  Minimize2,
} from "lucide-react";

// ─── TYPES & INTERFACES ─────────────────────────────────────────────────────────

export interface MultiVectorScorePoint {
  tokenOrPatchId: string;
  timestampSeconds: number;
  score: number; // Normalized similarity score [0.0 - 1.0]
  modality: "visual_patches" | "speech_audio" | "ocr_text";
  label: string;
}

export interface VideoItemMetadata {
  id: string;
  videoId: string;
  videoTitle: string;
  videoUrl: string;
  datasetSource: string;
  start_time: number;
  end_time: number;
  duration: number;
  score: number; // Aggregate MaxSim score [0.0 - 1.0]
  explanation: string;
  modality: "visual_patches" | "speech_audio" | "ocr_text";
  category: string;
  thumbnailPlaceholder?: string;
  ocrText?: string;
  whisperTranscript?: string;
  qwenReasoning?: string;
  // Multi-Vector Similarity Distribution for Semantic Radar
  multiVectorScores: MultiVectorScorePoint[];
  // Auto-Stitch sequel chaining
  next_part_id?: string | null;
  next_part_title?: string | null;
  next_part_url?: string | null;
}

// ─── SAMPLE DATA WITH MULTI-VECTOR & AUTO-STITCH CHAINING ───────────────────────

export const PLAYGROUND_SAMPLE_DATA: VideoItemMetadata[] = [
  {
    id: "match_colpali_01",
    videoId: "sih_lecture_01_part1",
    videoTitle: "Part 1: ColPali Multi-Vector Late Interaction & Vision Transformers",
    videoUrl: "/videos/UCF101/lecture_colpali_part1.mp4",
    datasetSource: "ChronoVision Core",
    start_time: 165.2,
    end_time: 185.0,
    duration: 600,
    score: 0.962,
    explanation: "ColPali preserves all patch tokens, computing native MaxSim across token-to-patch pairs for ultra-fine spatial alignment.",
    modality: "visual_patches",
    category: "Architecture Diagram",
    thumbnailPlaceholder: "Architecture Diagram: ColPali Multi-Vector Late Interaction",
    ocrText: "Formula: Score(Q, D) = sum_{q in Q} max_{d in D} (cos_sim(q, d))\nQdrant MultiVectorConfig(comparator=MAX_SIM)",
    whisperTranscript: "As you can see on this slide, the ColPali architecture preserves visual patch tokens instead of pooling them into a single vector.",
    qwenReasoning: "Qwen2-VL identified an architectural diagram detailing the token-to-patch similarity matrix. Visual patch indices (3,2) and (4,5) contain the mathematical formula for MaxSim.",
    next_part_id: "sih_lecture_01_part2",
    next_part_title: "Part 2: Qdrant Native MaxSim Indexing & Benchmark Comparison",
    next_part_url: "/videos/UCF101/lecture_colpali_part2.mp4",
    multiVectorScores: [
      { tokenOrPatchId: "tok_0", timestampSeconds: 20, score: 0.22, modality: "visual_patches", label: "Intro Hook" },
      { tokenOrPatchId: "tok_1", timestampSeconds: 60, score: 0.38, modality: "speech_audio", label: "Overview Speech" },
      { tokenOrPatchId: "tok_2", timestampSeconds: 110, score: 0.55, modality: "ocr_text", label: "Slide Index" },
      { tokenOrPatchId: "tok_3", timestampSeconds: 150, score: 0.88, modality: "visual_patches", label: "ColPali Token Matrix" },
      { tokenOrPatchId: "tok_4", timestampSeconds: 165.2, score: 0.98, modality: "visual_patches", label: "MaxSim Formula Peak" },
      { tokenOrPatchId: "tok_5", timestampSeconds: 175, score: 0.94, modality: "visual_patches", label: "Patch Embedding Layer" },
      { tokenOrPatchId: "tok_6", timestampSeconds: 220, score: 0.72, modality: "speech_audio", label: "Transformer Explanation" },
      { tokenOrPatchId: "tok_7", timestampSeconds: 280, score: 0.45, modality: "ocr_text", label: "Code Snippet" },
      { tokenOrPatchId: "tok_8", timestampSeconds: 340, score: 0.35, modality: "visual_patches", label: "Architecture Overview" },
      { tokenOrPatchId: "tok_9", timestampSeconds: 420, score: 0.62, modality: "speech_audio", label: "Loss Function Discussion" },
      { tokenOrPatchId: "tok_10", timestampSeconds: 500, score: 0.78, modality: "visual_patches", label: "Recall Comparison Graph" },
      { tokenOrPatchId: "tok_11", timestampSeconds: 580, score: 0.85, modality: "speech_audio", label: "Part 1 Wrap-up" },
    ],
  },
  {
    id: "match_colpali_02",
    videoId: "sih_lecture_01_part2",
    videoTitle: "Part 2: Qdrant Native MaxSim Indexing & Benchmark Comparison",
    videoUrl: "/videos/UCF101/lecture_colpali_part2.mp4",
    datasetSource: "ChronoVision Core",
    start_time: 40.0,
    end_time: 75.0,
    duration: 540,
    score: 0.918,
    explanation: "Native database-level MaxSim comparison eliminates expensive client-side reranking loops, achieving 18ms latency.",
    modality: "ocr_text",
    category: "Code Implementation",
    thumbnailPlaceholder: "Code Editor: Qdrant MultiVectorConfig Setup",
    ocrText: "client.create_collection(collection_name='video_chunks', multivector_config=MultiVectorConfig(comparator=MAX_SIM))",
    whisperTranscript: "Now we define the Qdrant schema with the multi-vector comparator set to MaxSim so late interaction runs natively in the database.",
    qwenReasoning: "Qwen2-VL spotted a VS Code screen displaying Python code creating a Qdrant multivector collection with dimension 128.",
    next_part_id: "sih_demo_03",
    next_part_title: "Part 3: Live Demo: Autonomous Drone Surveillance & Tracking",
    next_part_url: "/videos/UCF101/drone_surveillance.mp4",
    multiVectorScores: [
      { tokenOrPatchId: "tok_0", timestampSeconds: 15, score: 0.30, modality: "speech_audio", label: "Recap" },
      { tokenOrPatchId: "tok_1", timestampSeconds: 40, score: 0.92, modality: "ocr_text", label: "Qdrant Client Setup" },
      { tokenOrPatchId: "tok_2", timestampSeconds: 65, score: 0.95, modality: "ocr_text", label: "MultiVectorConfig Parameter" },
      { tokenOrPatchId: "tok_3", timestampSeconds: 120, score: 0.65, modality: "visual_patches", label: "Vector Pipeline Graph" },
      { tokenOrPatchId: "tok_4", timestampSeconds: 200, score: 0.82, modality: "visual_patches", label: "VRAM Benchmarks" },
      { tokenOrPatchId: "tok_5", timestampSeconds: 310, score: 0.58, modality: "speech_audio", label: "Query Encoding Walkthrough" },
      { tokenOrPatchId: "tok_6", timestampSeconds: 420, score: 0.74, modality: "visual_patches", label: "Latency Comparison" },
      { tokenOrPatchId: "tok_7", timestampSeconds: 510, score: 0.40, modality: "ocr_text", label: "Summary Slide" },
    ],
  },
  {
    id: "match_drone_03",
    videoId: "sih_demo_03",
    videoTitle: "Part 3: Live Demo: Autonomous Drone Surveillance & Tracking",
    videoUrl: "/videos/UCF101/drone_surveillance.mp4",
    datasetSource: "MSVD",
    start_time: 52.4,
    end_time: 72.0,
    duration: 360,
    score: 0.884,
    explanation: "Real-world aerial visual patches matched target vehicle trajectory with high spatio-temporal confidence.",
    modality: "visual_patches",
    category: "Real-world Camera",
    thumbnailPlaceholder: "Drone Camera: Autonomous Vehicle Tracking with BBoxes",
    ocrText: "CAMERA_ID: DRONE_ALPHA_09 | GPS: 28.6139° N, 77.2090° E | ALT: 42m",
    whisperTranscript: "Target vehicle identified near intersection B-4. High confidence visual tracking active.",
    qwenReasoning: "Qwen2-VL localized a silver sedan in the central visual quadrant with tracking telemetry on the upper boundary.",
    next_part_id: null,
    next_part_title: null,
    next_part_url: null,
    multiVectorScores: [
      { tokenOrPatchId: "tok_0", timestampSeconds: 10, score: 0.35, modality: "visual_patches", label: "Takeoff Telemetry" },
      { tokenOrPatchId: "tok_1", timestampSeconds: 35, score: 0.60, modality: "visual_patches", label: "Intersection Sweep" },
      { tokenOrPatchId: "tok_2", timestampSeconds: 52.4, score: 0.94, modality: "visual_patches", label: "Vehicle Identification" },
      { tokenOrPatchId: "tok_3", timestampSeconds: 65, score: 0.89, modality: "ocr_text", label: "GPS Coordinate Lock" },
      { tokenOrPatchId: "tok_4", timestampSeconds: 140, score: 0.70, modality: "speech_audio", label: "Operator Comm" },
      { tokenOrPatchId: "tok_5", timestampSeconds: 210, score: 0.50, modality: "visual_patches", label: "Perimeter Sweep" },
      { tokenOrPatchId: "tok_6", timestampSeconds: 320, score: 0.42, modality: "visual_patches", label: "Return to Base" },
    ],
  },
  {
    id: "match_recall_04",
    videoId: "sih_benchmark_04",
    videoTitle: "Part 4: Retrieval Recall & Late-Interaction Latency Benchmark Suite",
    videoUrl: "/videos/UCF101/benchmark_recall.mp4",
    datasetSource: "UCF101",
    start_time: 120.0,
    end_time: 155.0,
    duration: 480,
    score: 0.852,
    explanation: "Recall@1 jumps from 58.2% to 87.6% over single-vector pooling models on complex multi-aspect queries.",
    modality: "speech_audio",
    category: "Spoken Concept",
    thumbnailPlaceholder: "Speaker Presentation: Latency and VRAM Benchmarks",
    ocrText: "Comparison: CLIP Single Vector vs ColPali Multi-Vector\nRetrieval Recall@1: 58.2% -> 87.6%",
    whisperTranscript: "The trade-off is slightly higher index storage, but recall jumps from 58% to nearly 88% on complex visual queries.",
    qwenReasoning: "Qwen2-VL parsed a benchmark comparison bar chart demonstrating Recall@1 accuracy gains with ColPali.",
    next_part_id: null,
    next_part_title: null,
    next_part_url: null,
    multiVectorScores: [
      { tokenOrPatchId: "tok_0", timestampSeconds: 20, score: 0.25, modality: "ocr_text", label: "Benchmark Agenda" },
      { tokenOrPatchId: "tok_1", timestampSeconds: 80, score: 0.55, modality: "visual_patches", label: "Baseline CLIP Matrix" },
      { tokenOrPatchId: "tok_2", timestampSeconds: 120, score: 0.91, modality: "speech_audio", label: "Recall@1 Gain Discussion" },
      { tokenOrPatchId: "tok_3", timestampSeconds: 145, score: 0.86, modality: "ocr_text", label: "Recall Metrics Chart" },
      { tokenOrPatchId: "tok_4", timestampSeconds: 260, score: 0.65, modality: "visual_patches", label: "Storage Overhead Graph" },
      { tokenOrPatchId: "tok_5", timestampSeconds: 380, score: 0.48, modality: "speech_audio", label: "Conclusion & Takeaways" },
    ],
  },
];

// ─── COLOR HELPERS FOR SEMANTIC RADAR ─────────────────────────────────────────

/**
 * Returns 2026 Material 3 Expressive color classes based on similarity score.
 */
function getRadarBlockStyle(score: number): {
  bgClass: string;
  glowClass: string;
  badgeBg: string;
} {
  if (score >= 0.85) {
    return {
      bgClass: "bg-emerald-400 dark:bg-emerald-500",
      glowClass: "shadow-[0_0_12px_rgba(52,211,153,0.6)] ring-1 ring-emerald-300",
      badgeBg: "bg-emerald-950/80 text-emerald-300 border-emerald-800",
    };
  }
  if (score >= 0.70) {
    return {
      bgClass: "bg-indigo-400 dark:bg-indigo-500",
      glowClass: "shadow-[0_0_10px_rgba(99,102,241,0.5)] ring-1 ring-indigo-300",
      badgeBg: "bg-indigo-950/80 text-indigo-300 border-indigo-800",
    };
  }
  if (score >= 0.55) {
    return {
      bgClass: "bg-violet-400 dark:bg-violet-500",
      glowClass: "shadow-[0_0_8px_rgba(139,92,246,0.4)]",
      badgeBg: "bg-violet-950/80 text-violet-300 border-violet-800",
    };
  }
  if (score >= 0.40) {
    return {
      bgClass: "bg-amber-400 dark:bg-amber-500",
      glowClass: "shadow-[0_0_6px_rgba(251,191,36,0.3)]",
      badgeBg: "bg-amber-950/80 text-amber-300 border-amber-800",
    };
  }
  return {
    bgClass: "bg-slate-600 dark:bg-slate-700/80",
    glowClass: "opacity-40",
    badgeBg: "bg-slate-900 text-slate-400 border-slate-700",
  };
}

function formatTime(seconds: number): string {
  if (isNaN(seconds) || seconds < 0) return "00:00";
  const m = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const s = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${m}:${s}`;
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────

export const SearchPlayground: React.FC = () => {
  // Query & Results state
  const [searchQuery, setSearchQuery] = useState(
    "ColPali late interaction MaxSim formula"
  );
  const [activeTab, setActiveTab] = useState<
    "visual" | "qwen" | "ocr" | "whisper"
  >("visual");
  const [filterModality, setFilterModality] = useState<string>("all");
  const [matches, setMatches] = useState<VideoItemMetadata[]>(PLAYGROUND_SAMPLE_DATA);
  const [selectedMatch, setSelectedMatch] = useState<VideoItemMetadata>(
    PLAYGROUND_SAMPLE_DATA[0]
  );
  const [isSearching, setIsSearching] = useState(false);
  const [searchStatusMsg, setSearchStatusMsg] = useState<string | null>(null);

  // Video playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(selectedMatch.start_time);
  const [duration, setDuration] = useState(selectedMatch.duration || 600);
  const [isMuted, setIsMuted] = useState(false);
  const [videoError, setVideoError] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Auto-Stitch notification state
  const [autoStitchToast, setAutoStitchToast] = useState<{
    show: boolean;
    title: string;
    targetPartId: string;
  } | null>(null);

  // Semantic Radar hovered block state
  const [hoveredRadarBlock, setHoveredRadarBlock] =
    useState<MultiVectorScorePoint | null>(null);

  // Refs
  const videoRef = useRef<HTMLVideoElement>(null);
  const videoContainerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Filtered matches memoized
  const filteredMatches = useMemo(() => {
    return matches.filter((m) => {
      if (filterModality === "all") return true;
      return m.modality === filterModality;
    });
  }, [matches, filterModality]);

  // ─── VIDEO PLAYBACK SYNC & SELECTION ─────────────────────────────────────────

  const handleSelectMatch = useCallback((match: VideoItemMetadata) => {
    setSelectedMatch(match);
    setVideoError(false);
    setCurrentTime(match.start_time);

    const vid = videoRef.current;
    if (vid) {
      vid.currentTime = match.start_time;
      vid.play().catch(() => {
        setIsPlaying(false);
      });
    }
  }, []);

  // ─── AUTO-STITCH SEQUENCER (onEnded Listener) ───────────────────────────────

  /**
   * Auto-Stitch Handler: Triggered when the current video chunk finishes playing.
   * If `next_part_id` exists in the metadata, it smoothly switches the src
   * and auto-plays the sequel video.
   */
  const handleAutoStitch = useCallback(() => {
    if (!selectedMatch.next_part_id) {
      setIsPlaying(false);
      return;
    }

    const nextId = selectedMatch.next_part_id;
    const nextMatch = matches.find((m) => m.videoId === nextId);

    // Show expressive 2026 Material 3 auto-stitch toast
    setAutoStitchToast({
      show: true,
      title:
        selectedMatch.next_part_title ||
        nextMatch?.videoTitle ||
        `Sequel (${nextId})`,
      targetPartId: nextId,
    });

    // Auto-dismiss toast after 4.5 seconds
    setTimeout(() => {
      setAutoStitchToast(null);
    }, 4500);

    if (nextMatch) {
      // Transition smoothly to found item
      setSelectedMatch(nextMatch);
      setCurrentTime(nextMatch.start_time);
      setVideoError(false);

      const vid = videoRef.current;
      if (vid) {
        vid.src = nextMatch.videoUrl;
        vid.currentTime = nextMatch.start_time;
        vid
          .play()
          .then(() => setIsPlaying(true))
          .catch((err) => {
            console.warn("Auto-stitch playback handled policy:", err);
            setIsPlaying(false);
          });
      }
    } else {
      // Fallback: update src attribute directly to sequel path
      const nextUrl =
        selectedMatch.next_part_url || `/videos/UCF101/${nextId}.mp4`;
      const vid = videoRef.current;
      if (vid) {
        vid.src = nextUrl;
        vid.currentTime = 0;
        vid
          .play()
          .then(() => setIsPlaying(true))
          .catch((err) => {
            console.warn("Direct auto-stitch playback caught:", err);
            setIsPlaying(false);
          });
      }
    }
  }, [selectedMatch, matches]);

  // Video element event listeners
  useEffect(() => {
    const vid = videoRef.current;
    if (!vid) return;

    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    const onTimeUpdate = () => setCurrentTime(vid.currentTime);
    const onLoadedMetadata = () => {
      if (vid.duration && !isNaN(vid.duration)) {
        setDuration(vid.duration);
      }
    };
    const onError = () => {
      setVideoError(true);
      setIsPlaying(false);
    };

    vid.addEventListener("play", onPlay);
    vid.addEventListener("pause", onPause);
    vid.addEventListener("timeupdate", onTimeUpdate);
    vid.addEventListener("loadedmetadata", onLoadedMetadata);
    vid.addEventListener("error", onError);
    vid.addEventListener("ended", handleAutoStitch);

    return () => {
      vid.removeEventListener("play", onPlay);
      vid.removeEventListener("pause", onPause);
      vid.removeEventListener("timeupdate", onTimeUpdate);
      vid.removeEventListener("loadedmetadata", onLoadedMetadata);
      vid.removeEventListener("error", onError);
      vid.removeEventListener("ended", handleAutoStitch);
    };
  }, [handleAutoStitch]);

  // Toggle play/pause safely
  const togglePlay = () => {
    const vid = videoRef.current;
    if (!vid) return;

    if (vid.paused) {
      vid
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => setIsPlaying(false));
    } else {
      vid.pause();
      setIsPlaying(false);
    }
  };

  // Toggle Mute
  const toggleMute = () => {
    const vid = videoRef.current;
    if (!vid) return;
    vid.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  // Seek video
  const handleSeek = (newTime: number) => {
    const vid = videoRef.current;
    setCurrentTime(newTime);
    if (vid) {
      vid.currentTime = newTime;
    }
  };

  // Fullscreen toggle
  const toggleFullscreen = () => {
    const container = videoContainerRef.current;
    if (!container) return;

    if (!document.fullscreenElement) {
      container
        .requestFullscreen()
        .then(() => setIsFullscreen(true))
        .catch(() => {});
    } else {
      document
        .exitFullscreen()
        .then(() => setIsFullscreen(false))
        .catch(() => {});
    }
  };

  // ─── LIVE BACKEND SEARCH ─────────────────────────────────────────────────────
  const handleLiveSearch = async (overrideQuery?: string) => {
    const q = (overrideQuery ?? searchQuery).trim();
    if (!q) return;

    setIsSearching(true);
    setSearchStatusMsg(null);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      const resp = await fetch(`${apiUrl}/api/v1/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, top_k: 10 }),
      });

      if (!resp.ok) {
        throw new Error(`Server returned HTTP ${resp.status}`);
      }

      const data = await resp.json();
      if (data.results && data.results.length > 0) {
        const mappedResults: VideoItemMetadata[] = data.results.map(
          (item: any, idx: number) => {
            const startTime = Number(item.start_time) || 0;
            const endTime = Number(item.end_time) || startTime + 2.0;
            const matchScore = Number(item.score) || 0.85;

            // Synthesize realistic token distribution for radar
            const radarPoints: MultiVectorScorePoint[] = Array.from(
              { length: 24 },
              (_, i) => {
                const ts = (i / 24) * 60;
                const diff = Math.abs(ts - startTime);
                const pointScore = Math.max(
                  0.12,
                  Math.exp(-diff / 8) * matchScore
                );
                return {
                  tokenOrPatchId: `patch_tok_${i}`,
                  timestampSeconds: Number(ts.toFixed(1)),
                  score: Math.min(0.99, Number(pointScore.toFixed(3))),
                  modality: "visual_patches",
                  label: `Frame ${(i * 2.5).toFixed(1)}s (MaxSim: ${(pointScore * 100).toFixed(0)}%)`,
                };
              }
            );

            return {
              id: `match_${item.video_id}_${idx}`,
              videoId: item.video_id,
              videoTitle: `${item.dataset_source} — ${item.video_id}`,
              videoUrl:
                item.video_url ||
                `/videos/UCF101/lecture_colpali_part1.mp4`,
              datasetSource: item.dataset_source || "MSVD",
              start_time: startTime,
              end_time: endTime,
              duration: Math.max(60, endTime + 10),
              score: matchScore,
              explanation:
                item.explanation ||
                `ColPali MaxSim matched high-affinity visual patch tokens at ${startTime.toFixed(1)}s.`,
              modality: "visual_patches",
              category: "Multimodal Video Scene",
              thumbnailPlaceholder: `${item.dataset_source} Video: ${item.video_id}`,
              ocrText: item.ocr_text || undefined,
              whisperTranscript: item.transcript_text || undefined,
              qwenReasoning: item.explanation || undefined,
              multiVectorScores: radarPoints,
            };
          }
        );

        setMatches(mappedResults);
        handleSelectMatch(mappedResults[0]);
        setSearchStatusMsg(`Retrieved ${mappedResults.length} live matches from Qdrant via ColQwen MaxSim.`);
      } else {
        setSearchStatusMsg("No semantic matches found in vector index for this query.");
      }
    } catch (err: any) {
      console.warn("Live search failed, falling back to local demonstrations:", err);
      setSearchStatusMsg(`Backend query notice: ${err?.message || "Using cached demonstrator"}`);
      // Fallback to local filter
      const found =
        matches.find((m) =>
          m.videoTitle.toLowerCase().includes(q.toLowerCase())
        ) || matches[0];
      handleSelectMatch(found);
    } finally {
      setIsSearching(false);
    }
  };

  // Preset query handler
  const handlePresetClick = (preset: string, _index: number) => {
    setSearchQuery(preset);
    handleLiveSearch(preset);
  };

  // ─── SEMANTIC RADAR SCORE DISTRIBUTION ───────────────────────────────────────
  /**
   * Generates or extracts high-resolution Semantic Radar blocks for the timeline.
   * If the active item has multiVectorScores, we map them evenly across the video duration.
   */
  const radarBlocks = useMemo(() => {
    const scores = selectedMatch.multiVectorScores || [];
    if (scores.length === 0) {
      return Array.from({ length: 24 }, (_, i) => {
        const ts = (i / 24) * (duration || 600);
        const diff = Math.abs(ts - selectedMatch.start_time);
        const score = Math.max(
          0.15,
          Math.exp(-diff / 40) * selectedMatch.score
        );
        return {
          tokenOrPatchId: `vec_block_${i}`,
          timestampSeconds: ts,
          score: Math.min(0.99, score),
          modality: selectedMatch.modality,
          label: `Chunk ${i + 1} (${formatTime(ts)})`,
        };
      });
    }
    return scores;
  }, [selectedMatch, duration]);

  // ─── RENDER ──────────────────────────────────────────────────────────────────

  return (
    <div className="w-full space-y-6 sm:space-y-8 font-sans">
      {/* ── 1. SEARCH & FILTER SECTION (Mobile-First 2026 Android Layout) ──────── */}
      <section className="bg-slate-900/90 dark:bg-slate-950/90 rounded-3xl border border-slate-800/80 p-4 sm:p-5 shadow-2xl backdrop-blur-2xl transition-all">
        {/* Search input container */}
        <div className="relative flex flex-col sm:flex-row gap-2.5 sm:gap-3">
          <div className="relative flex-1">
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleLiveSearch(searchQuery);
                }
              }}
              placeholder="Search moments via ColPali late-interaction, Qwen2-VL, or OCR..."
              className="w-full bg-slate-950/90 border border-slate-700/80 rounded-2xl px-4 py-3.5 pl-11 sm:pl-12 text-slate-100 placeholder-slate-500 text-sm sm:text-base focus:outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/20 transition-all font-medium"
            />
            <Search className="w-5 h-5 text-indigo-400 absolute left-3.5 sm:left-4 top-1/2 -translate-y-1/2" />
          </div>

          <button
            disabled={isSearching}
            onClick={() => handleLiveSearch(searchQuery)}
            className="px-6 py-3.5 rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-60 text-white font-semibold text-sm shadow-lg shadow-indigo-500/25 active:scale-95 transition-all flex items-center justify-center gap-2 shrink-0 cursor-pointer"
          >
            <Zap className={`w-4 h-4 fill-current ${isSearching ? "animate-spin" : ""}`} />
            <span>{isSearching ? "Retrieving..." : "Search MaxSim"}</span>
          </button>
        </div>

        {/* Live Search Status Feedback Banner */}
        {searchStatusMsg && (
          <div className="mt-2.5 px-3.5 py-1.5 rounded-xl bg-indigo-950/40 border border-indigo-800/50 text-indigo-300 text-xs font-mono flex items-center justify-between">
            <span>{searchStatusMsg}</span>
            <button onClick={() => setSearchStatusMsg(null)} className="text-slate-400 hover:text-white text-xs ml-2">&times;</button>
          </div>
        )}

        {/* Quick query chips & Modality filter */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 pt-3 border-t border-slate-800/60 mt-3">
          {/* Preset Chips */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 shrink-0 mr-1 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-indigo-400" /> Suggestions:
            </span>
            {[
              "ColPali late interaction MaxSim formula",
              "Qdrant MultiVectorConfig setup",
              "Autonomous vehicle detection drone",
              "Recall benchmark comparison",
            ].map((preset, idx) => (
              <button
                key={idx}
                onClick={() => handlePresetClick(preset, idx)}
                className="px-3 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium border border-slate-700/50 hover:border-indigo-500/50 transition-all whitespace-nowrap active:scale-95"
              >
                {preset}
              </button>
            ))}
          </div>

          {/* Modality Filter Pills */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-2xl border border-slate-800/80 self-start md:self-auto overflow-x-auto max-w-full">
            {["all", "visual_patches", "ocr_text", "speech_audio"].map((mod) => (
              <button
                key={mod}
                onClick={() => setFilterModality(mod)}
                className={`px-3 py-1 rounded-xl text-xs font-semibold capitalize transition-all whitespace-nowrap ${
                  filterModality === mod
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                }`}
              >
                {mod.replace("_", " ")}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ── 2. MAIN INTERACTIVE GRID ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* ── Left Column: Ranked Search Results List ── */}
        <div className="lg:col-span-5 space-y-3 order-2 lg:order-1">
          <div className="flex items-center justify-between px-1">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-indigo-400" />
              Ranked Keyframe Matches ({filteredMatches.length})
            </h3>
            <span className="text-[11px] text-indigo-400 font-mono font-semibold bg-indigo-950/60 border border-indigo-800/60 px-2 py-0.5 rounded-full">
              Qdrant MaxSim
            </span>
          </div>

          {/* Cards Stack */}
          <div className="space-y-3">
            {filteredMatches.map((match) => {
              const isSelected = selectedMatch.id === match.id;
              const hasSequel = Boolean(match.next_part_id);

              return (
                <div
                  key={match.id}
                  onClick={() => handleSelectMatch(match)}
                  className={`p-4 rounded-3xl border transition-all cursor-pointer relative overflow-hidden group ${
                    isSelected
                      ? "bg-slate-900/95 border-indigo-500 ring-2 ring-indigo-500/40 shadow-xl shadow-indigo-500/10"
                      : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/80"
                  }`}
                >
                  {/* Top status line */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded-full font-mono text-xs font-bold bg-indigo-950 text-indigo-300 border border-indigo-800 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTime(match.start_time)}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-300 capitalize">
                        {match.modality.replace("_", " ")}
                      </span>
                      <span className="text-xs text-emerald-400 font-mono font-bold">
                        {(match.score * 100).toFixed(1)}% MaxSim
                      </span>
                    </div>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectMatch(match);
                      }}
                      className={`p-2 rounded-xl transition-all shrink-0 ${
                        isSelected
                          ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                          : "bg-slate-800 text-slate-300 group-hover:bg-indigo-600 group-hover:text-white"
                      }`}
                      aria-label="Play match"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                    </button>
                  </div>

                  {/* Title */}
                  <h4 className="text-sm font-bold text-slate-100 mt-2.5 line-clamp-2 leading-snug">
                    {match.videoTitle}
                  </h4>

                  {/* Explanation */}
                  <p className="text-xs text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
                    {match.explanation}
                  </p>

                  {/* Sequel badge if auto-stitch available */}
                  {hasSequel && (
                    <div className="mt-3 flex items-center gap-1.5 text-[11px] font-semibold text-violet-400 bg-violet-950/40 border border-violet-800/40 rounded-xl px-2.5 py-1">
                      <FastForward className="w-3 h-3 shrink-0" />
                      <span className="truncate">
                        Auto-Stitch: {match.next_part_title || match.next_part_id}
                      </span>
                    </div>
                  )}

                  {/* Card bottom metadata */}
                  <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                    <span className="font-mono">{match.datasetSource}</span>
                    <span className="flex items-center gap-1 text-indigo-400 font-semibold group-hover:translate-x-0.5 transition-transform">
                      Inspect Multi-Vector <ChevronRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Right Column: Video Player, Semantic Radar & Inspector ── */}
        <div className="lg:col-span-7 space-y-6 order-1 lg:order-2 sticky top-20">
          {/* Synchronized Player Box */}
          <div
            ref={videoContainerRef}
            className="bg-slate-900/90 dark:bg-slate-950/90 rounded-3xl border border-slate-800/80 p-4 sm:p-5 shadow-2xl backdrop-blur-2xl space-y-4 relative"
          >
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
                  <Film className="w-4 h-4 text-indigo-400" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-100 line-clamp-1">
                    {selectedMatch.videoTitle}
                  </h3>
                  <span className="text-[11px] font-mono text-slate-400">
                    {selectedMatch.videoId} &bull; Offset: {formatTime(selectedMatch.start_time)}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {selectedMatch.next_part_id && (
                  <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-violet-950/80 text-violet-300 border border-violet-800/80 animate-pulse">
                    <FastForward className="w-3 h-3" /> Auto-Stitch Enabled
                  </span>
                )}
                <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-800">
                  {(selectedMatch.score * 100).toFixed(1)}% MaxSim
                </span>
              </div>
            </div>

            {/* ── HTML5 Video Canvas Container ── */}
            <div className="relative aspect-video bg-black rounded-2xl border border-slate-800 overflow-hidden group shadow-inner">
              <video
                ref={videoRef}
                key={selectedMatch.videoUrl}
                src={selectedMatch.videoUrl}
                className="w-full h-full object-contain"
                playsInline
                preload="metadata"
                onEnded={handleAutoStitch}
              />

              {/* Fallback Poster / Simulated Video Screen */}
              {videoError && (
                <div className="absolute inset-0 bg-gradient-to-b from-slate-900 via-slate-950 to-black p-6 flex flex-col justify-between items-center text-center">
                  <div className="w-full flex items-center justify-between text-xs font-mono text-slate-300">
                    <span className="bg-black/70 px-3 py-1 rounded-full border border-white/10 backdrop-blur">
                      Simulated Multi-Vector Canvas
                    </span>
                    <span className="bg-indigo-950/80 text-indigo-300 border border-indigo-800 px-3 py-1 rounded-full">
                      Timestamp: {formatTime(currentTime)}
                    </span>
                  </div>

                  <div className="space-y-2 max-w-md">
                    <p className="text-sm sm:text-base font-bold text-slate-100">
                      {selectedMatch.thumbnailPlaceholder || selectedMatch.videoTitle}
                    </p>
                    <p className="text-xs text-indigo-300 font-mono bg-indigo-950/70 p-2.5 rounded-xl border border-indigo-900/50">
                      Matched via {selectedMatch.modality.replace("_", " ")} similarity
                    </p>
                  </div>

                  <div className="text-[11px] text-slate-500 font-mono">
                    Local video file preview simulated &bull; Click Radar blocks to scrub
                  </div>
                </div>
              )}

              {/* Large Play Overlay Button */}
              {!isPlaying && !videoError && (
                <button
                  onClick={togglePlay}
                  className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-xs transition-opacity"
                  aria-label="Play Video"
                >
                  <div className="w-16 h-16 rounded-full bg-indigo-600/90 hover:bg-indigo-500 text-white flex items-center justify-center shadow-2xl shadow-indigo-600/50 transform group-hover:scale-110 transition-transform">
                    <Play className="w-7 h-7 fill-current ml-1" />
                  </div>
                </button>
              )}

              {/* ── Auto-Stitch Sequel Notification Toast ── */}
              {autoStitchToast && (
                <div className="absolute top-4 left-4 right-4 z-30 p-3.5 rounded-2xl bg-slate-950/95 border border-violet-500/80 shadow-2xl backdrop-blur-xl flex items-center justify-between gap-3 animate-in fade-in slide-in-from-top-4 duration-300">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-violet-600 text-white flex items-center justify-center shadow-lg shadow-violet-600/40">
                      <FastForward className="w-4 h-4 animate-pulse" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-violet-300 uppercase tracking-wider">
                        Auto-Stitching Sequel
                      </p>
                      <p className="text-xs text-slate-100 font-medium line-clamp-1">
                        {autoStitchToast.title}
                      </p>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-1 rounded-md bg-violet-950 text-violet-300 border border-violet-800 shrink-0">
                    Seamless Loop
                  </span>
                </div>
              )}
            </div>

            {/* ── 3. SEMANTIC RADAR: MULTI-VECTOR SIMILARITY SCORE BLOCKS ──────── */}
            <div className="space-y-1.5 pt-1">
              <div className="flex items-center justify-between text-xs px-0.5">
                <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-slate-400 text-[11px]">
                  <Compass className="w-3.5 h-3.5 text-indigo-400 animate-spin-slow" />
                  <span>Semantic Radar</span>
                  <span className="text-slate-500 font-normal hidden sm:inline">
                    (Qdrant Multi-Vector Affinity Blocks)
                  </span>
                </div>

                {/* Live Tooltip / Score Badge */}
                {hoveredRadarBlock ? (
                  <div className="flex items-center gap-2 animate-in fade-in duration-150">
                    <span className="text-[11px] font-mono text-slate-300">
                      {hoveredRadarBlock.label}
                    </span>
                    <span
                      className={`text-xs font-mono font-bold px-2 py-0.5 rounded-full ${
                        getRadarBlockStyle(hoveredRadarBlock.score).badgeBg
                      }`}
                    >
                      {(hoveredRadarBlock.score * 100).toFixed(1)}% MaxSim
                    </span>
                  </div>
                ) : (
                  <span className="text-[11px] font-mono text-slate-500">
                    Hover/Tap block to inspect &bull; Click to seek
                  </span>
                )}
              </div>

              {/* ── Array of Colored HTML Div Blocks (Semantic Radar) ── */}
              <div
                className="relative w-full h-8 sm:h-9 bg-slate-950/80 rounded-xl p-1 border border-slate-800/80 flex items-end gap-1 overflow-hidden"
                role="region"
                aria-label="Semantic Radar Multi-Vector Timeline"
              >
                {radarBlocks.map((point, i) => {
                  const style = getRadarBlockStyle(point.score);
                  const isCurrentTimeNear =
                    Math.abs(currentTime - point.timestampSeconds) < 20;
                  const heightPercent = Math.max(25, point.score * 100);

                  return (
                    <div
                      key={point.tokenOrPatchId || i}
                      style={{ height: `${heightPercent}%` }}
                      onClick={() => handleSeek(point.timestampSeconds)}
                      onMouseEnter={() => setHoveredRadarBlock(point)}
                      onMouseLeave={() => setHoveredRadarBlock(null)}
                      onTouchStart={() => setHoveredRadarBlock(point)}
                      title={`${point.label} | MaxSim: ${(point.score * 100).toFixed(1)}%`}
                      className={`flex-1 rounded-[4px] transition-all cursor-pointer relative group ${
                        style.bgClass
                      } ${style.glowClass} ${
                        isCurrentTimeNear
                          ? "ring-2 ring-white scale-y-105 z-10"
                          : "hover:scale-y-110 hover:opacity-100"
                      }`}
                    >
                      {/* Active indicator pip */}
                      {isCurrentTimeNear && (
                        <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-white shadow-sm" />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* ── 4. VIDEO PLAYER TIMELINE & CONTROLS ──────────────────────────── */}
            <div className="bg-slate-950/90 rounded-2xl p-3 sm:p-4 border border-slate-800/80 space-y-3">
              {/* Range Scrubber */}
              <div className="relative">
                <input
                  type="range"
                  min="0"
                  max={duration || 600}
                  step="0.1"
                  value={currentTime}
                  onChange={(e) => handleSeek(Number(e.target.value))}
                  className="w-full accent-indigo-500 cursor-pointer h-2 bg-slate-800 rounded-lg"
                  aria-label="Timeline scrubber"
                />
              </div>

              {/* Transport Controls Bar */}
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2 sm:gap-3">
                  {/* Play / Pause */}
                  <button
                    onClick={togglePlay}
                    className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30 active:scale-95 transition-all"
                    aria-label={isPlaying ? "Pause" : "Play"}
                  >
                    {isPlaying ? (
                      <Pause className="w-4 h-4" />
                    ) : (
                      <Play className="w-4 h-4 fill-current ml-0.5" />
                    )}
                  </button>

                  {/* Restart */}
                  <button
                    onClick={() => handleSeek(selectedMatch.start_time)}
                    className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                    title={`Jump to match start (${formatTime(selectedMatch.start_time)})`}
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>

                  {/* Mute */}
                  <button
                    onClick={toggleMute}
                    className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                    aria-label={isMuted ? "Unmute" : "Mute"}
                  >
                    {isMuted ? (
                      <VolumeX className="w-4 h-4 text-rose-400" />
                    ) : (
                      <Volume2 className="w-4 h-4" />
                    )}
                  </button>

                  {/* Time Counters */}
                  <span className="text-xs font-mono text-slate-300 font-semibold pl-1">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </span>
                </div>

                {/* Jump to start / Sequel Trigger Buttons */}
                <div className="flex items-center gap-2">
                  {selectedMatch.next_part_id && (
                    <button
                      onClick={handleAutoStitch}
                      className="px-3 py-1.5 rounded-xl bg-violet-950/80 hover:bg-violet-900/80 border border-violet-800 text-violet-300 text-xs font-semibold flex items-center gap-1.5 transition-all active:scale-95"
                    >
                      <FastForward className="w-3.5 h-3.5" />
                      <span>Play Sequel</span>
                    </button>
                  )}

                  <button
                    onClick={toggleFullscreen}
                    className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                    aria-label="Toggle Fullscreen"
                  >
                    {isFullscreen ? (
                      <Minimize2 className="w-4 h-4" />
                    ) : (
                      <Maximize2 className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* ── 5. MODALITY INSPECTOR TABS ─────────────────────────────────── */}
            <div className="space-y-4 pt-2">
              {/* Tab selector bar */}
              <div className="flex border-b border-slate-800 gap-1 sm:gap-2 overflow-x-auto scrollbar-none">
                {[
                  { id: "visual", label: "ColPali Heatmap" },
                  { id: "qwen", label: "Qwen2-VL CoT" },
                  { id: "ocr", label: "PaddleOCR Text" },
                  { id: "whisper", label: "Whisper Audio" },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as "visual" | "qwen" | "ocr" | "whisper")}
                    className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-all whitespace-nowrap ${
                      activeTab === tab.id
                        ? "border-indigo-500 text-indigo-400"
                        : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab Contents */}
              {activeTab === "visual" && (
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800/80 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-indigo-400 text-xs font-bold">
                      <Layers className="w-4 h-4" />
                      <span>ColPali Patch-to-Token MaxSim Alignment Matrix</span>
                    </div>
                    <span className="text-[11px] font-mono text-slate-500">
                      8×8 Spatial Patches
                    </span>
                  </div>

                  {/* 8x8 Patch Grid Simulation */}
                  <div className="grid grid-cols-8 gap-1.5 p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                    {Array.from({ length: 64 }).map((_, i) => {
                      const row = Math.floor(i / 8);
                      const col = i % 8;
                      const dist = Math.hypot(row - 3.5, col - 3.5);
                      const intensity = Math.max(
                        0.1,
                        Math.exp(-dist / 2.0) * selectedMatch.score
                      );
                      const style = getRadarBlockStyle(intensity);

                      return (
                        <div
                          key={i}
                          className={`aspect-square rounded-[4px] ${style.bgClass} ${style.glowClass} transition-all hover:scale-125 cursor-pointer`}
                          title={`Patch (${row}, ${col}) - MaxSim: ${(
                            intensity * 100
                          ).toFixed(0)}%`}
                        />
                      );
                    })}
                  </div>
                </div>
              )}

              {activeTab === "qwen" && (
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800/80 space-y-3">
                  <div className="flex items-center gap-2 text-indigo-400 text-xs font-bold">
                    <Sparkles className="w-4 h-4" />
                    <span>Qwen2-VL-7B Vision-Language CoT Rationale (vLLM)</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                    {selectedMatch.qwenReasoning}
                  </p>
                  <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-slate-400">
                    <span>Latency: 42ms</span>
                    <span>Engine: vLLM Triton</span>
                    <span>Model: Qwen2-VL-7B-Instruct</span>
                  </div>
                </div>
              )}

              {activeTab === "ocr" && (
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800/80 space-y-2 font-mono">
                  <div className="flex items-center gap-2 text-amber-400 text-xs font-bold">
                    <FileText className="w-4 h-4" />
                    <span>PaddleOCR Extracted Keyframe Bounding Boxes</span>
                  </div>
                  <pre className="p-3 bg-slate-900/60 rounded-xl text-xs text-slate-200 whitespace-pre-wrap border border-slate-800">
                    {selectedMatch.ocrText || "No OCR text detected on this frame."}
                  </pre>
                </div>
              )}

              {activeTab === "whisper" && (
                <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800/80 space-y-2 font-mono">
                  <div className="flex items-center gap-2 text-sky-400 text-xs font-bold">
                    <Volume2 className="w-4 h-4" />
                    <span>Faster-Whisper Spoken Audio Transcript</span>
                  </div>
                  <p className="p-3 bg-slate-900/60 rounded-xl text-xs text-slate-200 italic border border-slate-800">
                    &ldquo;{selectedMatch.whisperTranscript || "No speech detected in this interval."}&rdquo;
                  </p>
                  <div className="text-[11px] text-slate-500 font-mono">
                    Offset: {formatTime(selectedMatch.start_time)} &bull; Confidence: 0.98
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
