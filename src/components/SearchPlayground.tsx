import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import {
  Search,
  Sparkles,
  Video,
  Volume2,
  VolumeX,
  FileText,
  Play,
  Pause,
  RotateCcw,
  SlidersHorizontal,
  CheckCircle2,
  ChevronRight,
  Zap,
  FastForward,
  Compass,
  Layers,
  Activity,
  Film,
  Maximize2,
  Minimize2
} from 'lucide-react';
import { sampleKeyframeMatches } from '../data/sampleVideos';
import { VideoKeyframeMatch, MultiVectorScorePoint } from '../types';
import { LateInteractionHeatmap } from './LateInteractionHeatmap';

/**
 * 2026 Material 3 Expressive color token mapping for Semantic Radar
 */
function getRadarBlockStyle(score: number): {
  bgClass: string;
  glowClass: string;
  badgeBg: string;
} {
  if (score >= 0.85) {
    return {
      bgClass: 'bg-emerald-400 dark:bg-emerald-500',
      glowClass: 'shadow-[0_0_12px_rgba(52,211,153,0.6)] ring-1 ring-emerald-300',
      badgeBg: 'bg-emerald-950/80 text-emerald-300 border-emerald-800',
    };
  }
  if (score >= 0.70) {
    return {
      bgClass: 'bg-indigo-400 dark:bg-indigo-500',
      glowClass: 'shadow-[0_0_10px_rgba(99,102,241,0.5)] ring-1 ring-indigo-300',
      badgeBg: 'bg-indigo-950/80 text-indigo-300 border-indigo-800',
    };
  }
  if (score >= 0.55) {
    return {
      bgClass: 'bg-violet-400 dark:bg-violet-500',
      glowClass: 'shadow-[0_0_8px_rgba(139,92,246,0.4)]',
      badgeBg: 'bg-violet-950/80 text-violet-300 border-violet-800',
    };
  }
  if (score >= 0.40) {
    return {
      bgClass: 'bg-amber-400 dark:bg-amber-500',
      glowClass: 'shadow-[0_0_6px_rgba(251,191,36,0.3)]',
      badgeBg: 'bg-amber-950/80 text-amber-300 border-amber-800',
    };
  }
  return {
    bgClass: 'bg-slate-700',
    glowClass: 'opacity-40',
    badgeBg: 'bg-slate-900 text-slate-400 border-slate-700',
  };
}

function formatTime(seconds: number): string {
  if (isNaN(seconds) || seconds < 0) return "00:00";
  const m = Math.floor(seconds / 60).toString().padStart(2, "0");
  const s = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

export const SearchPlayground: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('ColPali late interaction MaxSim formula');
  const [selectedMatch, setSelectedMatch] = useState<VideoKeyframeMatch>(sampleKeyframeMatches[0]);
  const [activeTab, setActiveTab] = useState<'visual' | 'qwen' | 'ocr' | 'whisper'>('visual');
  const [filterModality, setFilterModality] = useState<string>('all');
  
  // Video playback & timeline state
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackTime, setPlaybackTime] = useState<number>(selectedMatch.timestampSeconds);
  const [duration, setDuration] = useState<number>(600);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Auto-Stitch sequel state
  const [autoStitchToast, setAutoStitchToast] = useState<{
    show: boolean;
    title: string;
    targetPartId: string;
  } | null>(null);

  // Hovered Semantic Radar block for tooltips
  const [hoveredRadarBlock, setHoveredRadarBlock] = useState<MultiVectorScorePoint | null>(null);

  // Video element & container refs
  const videoRef = useRef<HTMLVideoElement>(null);
  const videoContainerRef = useRef<HTMLDivElement>(null);

  const filteredMatches = useMemo(() => {
    return sampleKeyframeMatches.filter(m => {
      if (filterModality === 'all') return true;
      return m.modality === filterModality;
    });
  }, [filterModality]);

  // Select a match and seek video
  const handleSelectMatch = useCallback((match: VideoKeyframeMatch) => {
    setSelectedMatch(match);
    setPlaybackTime(match.timestampSeconds);

    const vid = videoRef.current;
    if (vid) {
      vid.currentTime = match.timestampSeconds;
      vid.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
    }
  }, []);

  // ── Auto-Stitch Sequencer Handler ─────────────────────────────────────────
  const handleAutoStitch = useCallback(() => {
    if (!selectedMatch.next_part_id) {
      setIsPlaying(false);
      return;
    }

    const nextId = selectedMatch.next_part_id;
    const nextMatch = sampleKeyframeMatches.find(m => m.videoId === nextId);

    setAutoStitchToast({
      show: true,
      title: selectedMatch.next_part_title || nextMatch?.videoTitle || `Sequel (${nextId})`,
      targetPartId: nextId,
    });

    setTimeout(() => {
      setAutoStitchToast(null);
    }, 4500);

    if (nextMatch) {
      setSelectedMatch(nextMatch);
      setPlaybackTime(nextMatch.timestampSeconds);

      const vid = videoRef.current;
      if (vid) {
        vid.src = nextMatch.videoUrl || `/videos/UCF101/${nextId}.mp4`;
        vid.currentTime = nextMatch.timestampSeconds;
        vid.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
      }
    }
  }, [selectedMatch]);

  // Sync video HTML5 element events
  useEffect(() => {
    const vid = videoRef.current;
    if (!vid) return;

    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    const onTimeUpdate = () => setPlaybackTime(vid.currentTime);
    const onLoadedMetadata = () => {
      if (vid.duration && !isNaN(vid.duration)) {
        setDuration(vid.duration);
      }
    };
    const onEnded = () => handleAutoStitch();

    vid.addEventListener('play', onPlay);
    vid.addEventListener('pause', onPause);
    vid.addEventListener('timeupdate', onTimeUpdate);
    vid.addEventListener('loadedmetadata', onLoadedMetadata);
    vid.addEventListener('ended', onEnded);

    return () => {
      vid.removeEventListener('play', onPlay);
      vid.removeEventListener('pause', onPause);
      vid.removeEventListener('timeupdate', onTimeUpdate);
      vid.removeEventListener('loadedmetadata', onLoadedMetadata);
      vid.removeEventListener('ended', onEnded);
    };
  }, [handleAutoStitch]);

  // Video controls
  const togglePlay = () => {
    const vid = videoRef.current;
    if (!vid) return;
    if (vid.paused) {
      vid.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
    } else {
      vid.pause();
      setIsPlaying(false);
    }
  };

  const handleSeek = (time: number) => {
    setPlaybackTime(time);
    const vid = videoRef.current;
    if (vid) {
      vid.currentTime = time;
    }
  };

  const toggleFullscreen = () => {
    const container = videoContainerRef.current;
    if (!container) return;
    if (!document.fullscreenElement) {
      container.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  // Extract multi-vector similarity points for Semantic Radar
  const radarBlocks = useMemo(() => {
    if (selectedMatch.multiVectorScores && selectedMatch.multiVectorScores.length > 0) {
      return selectedMatch.multiVectorScores;
    }
    return Array.from({ length: 24 }, (_, i) => {
      const ts = (i / 24) * duration;
      const diff = Math.abs(ts - selectedMatch.timestampSeconds);
      const score = Math.max(0.15, Math.exp(-diff / 40) * selectedMatch.score);
      return {
        tokenOrPatchId: `vec_${i}`,
        timestampSeconds: ts,
        score: Math.min(0.99, score),
        modality: selectedMatch.modality,
        label: `Vector Segment ${i + 1} (${formatTime(ts)})`,
      };
    });
  }, [selectedMatch, duration]);

  return (
    <div className="space-y-5 sm:space-y-6 w-full min-w-0">
      {/* ── Search Input & Modality Filter Bar (Mobile First) ── */}
      <div className="bg-slate-900/90 rounded-3xl border border-slate-800 p-4 sm:p-5 shadow-xl backdrop-blur-xl space-y-3">
        <div className="relative flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search video timestamps by semantic visuals, spoken audio, or OCR..."
              className="w-full bg-slate-950 border border-slate-700/80 rounded-2xl px-4 py-3.5 pl-11 text-slate-100 placeholder-slate-500 text-sm sm:text-base focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 font-sans"
            />
            <Search className="w-5 h-5 text-indigo-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          </div>

          <button
            onClick={() => {
              const found = sampleKeyframeMatches.find(m =>
                m.videoTitle.toLowerCase().includes(searchQuery.toLowerCase())
              ) || sampleKeyframeMatches[0];
              handleSelectMatch(found);
            }}
            className="px-5 py-3.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-md shadow-indigo-600/30 flex items-center justify-center gap-2 active:scale-95 transition-all shrink-0"
          >
            <Zap className="w-4 h-4 fill-current" />
            <span>Search</span>
          </button>
        </div>

        {/* Quick query chips & Modality filter */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 text-xs pt-2 border-t border-slate-800/60">
          <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
            <span className="text-slate-400 font-semibold uppercase tracking-wider text-[11px] shrink-0">
              Suggestions:
            </span>
            {[
              'ColPali late interaction MaxSim formula',
              'Qdrant MultiVectorConfig indexing setup',
              'Autonomous vehicle detection drone',
              'Recall benchmark comparison'
            ].map((preset, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setSearchQuery(preset);
                  const found = sampleKeyframeMatches[idx] || sampleKeyframeMatches[0];
                  handleSelectMatch(found);
                }}
                className="px-3 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors whitespace-nowrap active:scale-95"
              >
                {preset}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-2xl border border-slate-800 self-start md:self-auto overflow-x-auto">
            {['all', 'visual_patches', 'ocr_text', 'speech_audio'].map((mod) => (
              <button
                key={mod}
                onClick={() => setFilterModality(mod)}
                className={`px-3 py-1 rounded-xl text-xs capitalize transition-all whitespace-nowrap ${
                  filterModality === mod
                    ? 'bg-indigo-600 text-white font-semibold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {mod.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Main Interactive Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 sm:gap-6 items-start">
        {/* Left Column: Ranked Matches (lg:col-span-5) */}
        <div className="lg:col-span-5 space-y-3 order-2 lg:order-1">
          <div className="flex items-center justify-between px-1">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-indigo-400" />
              Ranked Keyframe Matches ({filteredMatches.length})
            </h3>
            <span className="text-xs text-indigo-400 font-mono">M2 Late-Interaction Ranked</span>
          </div>

          <div className="space-y-3">
            {filteredMatches.map((match) => {
              const isSelected = selectedMatch.id === match.id;
              const hasSequel = Boolean(match.next_part_id);

              return (
                <div
                  key={match.id}
                  onClick={() => handleSelectMatch(match)}
                  style={{ animationDelay: `${filteredMatches.indexOf(match) * 80}ms` }}
                  className={`p-4 rounded-3xl border transition-all duration-500 ease-out cursor-pointer relative overflow-hidden group animate-slide-up hover:-translate-y-1 hover:scale-[1.01] hover:shadow-[0_12px_35px_rgba(79,70,229,0.16)] ${
                    isSelected
                      ? 'bg-slate-900 border-indigo-500 ring-2 ring-indigo-500/50 shadow-xl shadow-indigo-500/10 scale-[1.01]'
                      : 'bg-slate-900/60 border-slate-800 hover:border-indigo-500/50'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="px-2.5 py-0.5 rounded-full font-mono text-xs font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
                          {match.timestampFormatted}
                        </span>
                        <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-300 capitalize">
                          {match.modality.replace('_', ' ')}
                        </span>
                        <span className="text-xs text-emerald-400 font-mono font-bold">
                          {(match.score * 100).toFixed(1)}% MaxSim
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-100 mt-2 line-clamp-1">
                        {match.videoTitle}
                      </h4>
                    </div>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectMatch(match);
                        setIsPlaying(true);
                      }}
                      className="p-2 rounded-xl bg-slate-800 hover:bg-indigo-600 text-slate-300 hover:text-white transition-colors shrink-0 active:scale-95"
                    >
                      <Play className="w-4 h-4 fill-current" />
                    </button>
                  </div>

                  <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                    {match.ocrExtractedText.replace(/\n/g, ' ')}
                  </p>

                  {hasSequel && (
                    <div className="mt-2.5 flex items-center gap-1.5 text-[11px] font-semibold text-violet-400 bg-violet-950/40 border border-violet-800/40 rounded-xl px-2.5 py-1">
                      <FastForward className="w-3 h-3 shrink-0" />
                      <span className="truncate">Auto-Stitch: {match.next_part_title || match.next_part_id}</span>
                    </div>
                  )}

                  <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
                    <span className="font-mono">{match.category}</span>
                    <span className="flex items-center gap-1 text-indigo-400 font-medium">
                      Inspect Frame <ChevronRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Video Synchronizer & Radar Inspector (lg:col-span-7) */}
        <div className="lg:col-span-7 space-y-5 sm:space-y-6 order-1 lg:order-2 lg:sticky lg:top-20">
          <div
            ref={videoContainerRef}
            className="bg-slate-900/90 rounded-3xl border border-slate-800 p-3 sm:p-5 shadow-xl space-y-4 relative backdrop-blur-xl animate-content-in"
          >
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Video className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-slate-100 line-clamp-1">
                  Synchronized Frame Player ({formatTime(playbackTime)})
                </h3>
              </div>
              <div className="flex items-center gap-2">
                {selectedMatch.next_part_id && (
                  <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-violet-950 text-violet-300 border border-violet-800 animate-pulse">
                    <FastForward className="w-3 h-3" /> Auto-Stitch Enabled
                  </span>
                )}
                <span className="text-xs font-mono text-slate-400">{selectedMatch.videoId}</span>
              </div>
            </div>

            {/* Video Canvas Box */}
            <div className="aspect-[9/16] sm:aspect-video bg-slate-950 rounded-2xl border border-slate-800 relative overflow-hidden flex flex-col justify-between p-3 sm:p-4 shadow-inner transition-all duration-500">
              <video
                ref={videoRef}
                key={selectedMatch.videoUrl || selectedMatch.videoId}
                src={selectedMatch.videoUrl || `/videos/UCF101/${selectedMatch.videoId}.mp4`}
                className="w-full h-full object-contain absolute inset-0 z-0"
                playsInline
                preload="metadata"
                onEnded={handleAutoStitch}
              />

              <div className="relative z-10 flex items-center justify-between text-xs font-mono text-slate-300">
                <span className="bg-black/70 px-2.5 py-1 rounded-full backdrop-blur border border-white/10">
                  {selectedMatch.videoTitle}
                </span>
                <span className="bg-emerald-950/80 text-emerald-300 border border-emerald-800 px-2.5 py-1 rounded-full">
                  MaxSim: {(selectedMatch.score * 100).toFixed(1)}%
                </span>
              </div>

              <div className="relative z-10 text-center p-4 bg-slate-900/80 rounded-2xl border border-slate-800 backdrop-blur max-w-md mx-auto my-auto pointer-events-none">
                <p className="text-sm font-semibold text-slate-100">{selectedMatch.thumbnailPlaceholder}</p>
                <p className="text-xs text-indigo-300 font-mono mt-1.5 bg-indigo-950/60 p-2 rounded-xl border border-indigo-900/40">
                  Matched via {selectedMatch.modality.replace('_', ' ')} alignment
                </p>
              </div>

              {/* Auto-Stitch Sequel Toast */}
              {autoStitchToast && (
                <div className="absolute top-4 left-4 right-4 z-30 p-3 rounded-2xl bg-slate-950/95 border border-violet-500/80 shadow-2xl backdrop-blur-xl flex items-center justify-between gap-3 animate-in fade-in duration-300">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-violet-600 text-white flex items-center justify-center">
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
                  <span className="text-[10px] font-mono px-2 py-1 rounded-md bg-violet-950 text-violet-300 border border-violet-800">
                    Looping
                  </span>
                </div>
              )}
            </div>

            {/* ── SEMANTIC RADAR (Multi-Vector Blocks above Timeline) ── */}
            <div className="space-y-1.5 pt-1">
              <div className="flex items-center justify-between text-xs px-0.5">
                <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-slate-400 text-[11px]">
                  <Compass className="w-3.5 h-3.5 text-indigo-400 animate-spin-slow" />
                  <span>Semantic Radar</span>
                </div>

                {hoveredRadarBlock ? (
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-slate-300">{hoveredRadarBlock.label}</span>
                    <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded-full ${getRadarBlockStyle(hoveredRadarBlock.score).badgeBg}`}>
                      {(hoveredRadarBlock.score * 100).toFixed(1)}% MaxSim
                    </span>
                  </div>
                ) : (
                  <span className="text-[11px] font-mono text-slate-500">
                    Hover/Tap block to inspect &bull; Click to seek
                  </span>
                )}
              </div>

              {/* Radar HTML Div Blocks */}
              <div
                className="relative w-full h-8 sm:h-9 bg-slate-950 rounded-xl p-1 border border-slate-800 flex items-end gap-1 overflow-hidden"
                role="region"
                aria-label="Semantic Radar Multi-Vector Timeline"
              >
                {radarBlocks.map((pt, i) => {
                  const style = getRadarBlockStyle(pt.score);
                  const isCurrentTimeNear = Math.abs(playbackTime - pt.timestampSeconds) < 20;
                  const heightPercent = Math.max(25, pt.score * 100);

                  return (
                    <div
                      key={pt.tokenOrPatchId || i}
                      style={{ height: `${heightPercent}%` }}
                      onClick={() => handleSeek(pt.timestampSeconds)}
                      onMouseEnter={() => setHoveredRadarBlock(pt)}
                      onMouseLeave={() => setHoveredRadarBlock(null)}
                      onTouchStart={() => setHoveredRadarBlock(pt)}
                      title={`${pt.label} | MaxSim: ${(pt.score * 100).toFixed(1)}%`}
                      className={`flex-1 rounded-[4px] transition-all duration-300 cursor-pointer relative hover:-translate-y-0.5 ${
                        style.bgClass
                      } ${style.glowClass} ${
                        isCurrentTimeNear
                          ? 'ring-2 ring-white scale-y-105 z-10'
                          : 'hover:scale-y-110 hover:opacity-100'
                      }`}
                    >
                      {isCurrentTimeNear && (
                        <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-white shadow-sm" />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* ── Timeline Transport Controls ── */}
            <div className="bg-slate-950/90 rounded-2xl p-3 sm:p-4 border border-slate-800 space-y-3">
              <div className="relative">
                <input
                  type="range"
                  min="0"
                  max={duration || 600}
                  step="0.1"
                  value={playbackTime}
                  onChange={(e) => handleSeek(Number(e.target.value))}
                  className="w-full accent-indigo-500 cursor-pointer h-2 bg-slate-800 rounded-lg"
                  aria-label="Playback timeline"
                />
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2 sm:gap-3">
                  <button
                    onClick={togglePlay}
                    className="p-2.5 rounded-xl bg-indigo-600 text-white hover:bg-indigo-500 active:scale-95 transition-all shrink-0 shadow-md shadow-indigo-600/30"
                    aria-label={isPlaying ? 'Pause' : 'Play'}
                  >
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
                  </button>

                  <button
                    onClick={() => handleSeek(selectedMatch.timestampSeconds)}
                    className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                    title={`Jump to match start (${selectedMatch.timestampFormatted})`}
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() => {
                      const vid = videoRef.current;
                      if (vid) {
                        vid.muted = !isMuted;
                        setIsMuted(!isMuted);
                      }
                    }}
                    className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                  >
                    {isMuted ? <VolumeX className="w-4 h-4 text-rose-400" /> : <Volume2 className="w-4 h-4" />}
                  </button>

                  <span className="text-xs font-mono text-slate-300 font-semibold pl-1">
                    {formatTime(playbackTime)} / {formatTime(duration)}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {selectedMatch.next_part_id && (
                    <button
                      onClick={handleAutoStitch}
                      className="px-3 py-1.5 rounded-xl bg-violet-950/80 hover:bg-violet-900 border border-violet-800 text-violet-300 text-xs font-semibold flex items-center gap-1.5 transition-all active:scale-95"
                    >
                      <FastForward className="w-3.5 h-3.5" />
                      <span>Play Sequel</span>
                    </button>
                  )}

                  <button
                    onClick={toggleFullscreen}
                    className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                  >
                    {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>

            {/* Modality Inspection Tabs */}
            <div className="flex border-b border-slate-800 gap-2 overflow-x-auto scrollbar-none">
              <button
                onClick={() => setActiveTab('visual')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === 'visual'
                    ? 'border-indigo-500 text-indigo-400 font-semibold'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                M2 ColPali Heatmap
              </button>
              <button
                onClick={() => setActiveTab('qwen')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === 'qwen'
                    ? 'border-indigo-500 text-indigo-400 font-semibold'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                M1 Qwen2-VL Reasoning
              </button>
              <button
                onClick={() => setActiveTab('ocr')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === 'ocr'
                    ? 'border-indigo-500 text-indigo-400 font-semibold'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                M3 PaddleOCR Extracted
              </button>
              <button
                onClick={() => setActiveTab('whisper')}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === 'whisper'
                    ? 'border-indigo-500 text-indigo-400 font-semibold'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                M3 Whisper Transcript
              </button>
            </div>

            {/* Tab Contents */}
            {activeTab === 'visual' && (
              <LateInteractionHeatmap match={selectedMatch} />
            )}

            {activeTab === 'qwen' && (
              <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-3">
                <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold">
                  <Sparkles className="w-4 h-4" />
                  Qwen2-VL-7B Vision-Language CoT Reasoning (vLLM Engine)
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                  {selectedMatch.qwenReasoning}
                </p>
                <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-slate-400">
                  <span>Inference Latency: 42ms</span>
                  <span>vLLM Engine: Enabled</span>
                  <span>Model: Qwen2-VL-7B-Instruct</span>
                </div>
              </div>
            )}

            {activeTab === 'ocr' && (
              <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-2 font-mono">
                <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold">
                  <FileText className="w-4 h-4" />
                  Keyframe OCR Bounding Box Text (PaddleOCR)
                </div>
                <pre className="p-3 bg-slate-900 rounded-xl text-xs text-slate-200 whitespace-pre-wrap border border-slate-800">
                  {selectedMatch.ocrExtractedText}
                </pre>
              </div>
            )}

            {activeTab === 'whisper' && (
              <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-2 font-mono">
                <div className="flex items-center gap-2 text-sky-400 text-xs font-semibold">
                  <Volume2 className="w-4 h-4" />
                  Audio Speech Transcript (Faster-Whisper with Timestamps)
                </div>
                <p className="p-3 bg-slate-900 rounded-xl text-xs text-slate-200 italic border border-slate-800">
                  "{selectedMatch.whisperTranscript}"
                </p>
                <div className="text-[11px] text-slate-500 font-mono">
                  Timestamp Offset: {selectedMatch.timestampFormatted} &bull; Confidence: 0.96
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
