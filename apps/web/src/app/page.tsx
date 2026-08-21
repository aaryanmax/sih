"use client";

import React, {
  useState,
  useRef,
  useCallback,
  useEffect,
  KeyboardEvent,
} from "react";
import {
  Search,
  Sparkles,
  Play,
  Pause,
  Clock,
  Database,
  Layers,
  Film,
  AlertCircle,
  Loader2,
  ChevronRight,
  Volume2,
  FileText,
  Zap,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface SearchResult {
  video_id: string;
  video_url: string;
  start_time: number;
  end_time: number;
  score: number;
  explanation: string;
  dataset_source: string;
  transcript_text?: string | null;
  ocr_text?: string | null;
}

interface SearchResponse {
  query: string;
  total: number;
  results: SearchResult[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function formatTime(secs: number): string {
  const m = Math.floor(secs / 60)
    .toString()
    .padStart(2, "0");
  const s = Math.floor(secs % 60)
    .toString()
    .padStart(2, "0");
  return `${m}:${s}`;
}

function scoreColor(score: number): string {
  if (score >= 0.8) return "text-emerald-400";
  if (score >= 0.6) return "text-indigo-400";
  if (score >= 0.4) return "text-amber-400";
  return "text-rose-400";
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div className="glass rounded-2xl p-5 space-y-3">
      <div className="flex gap-3">
        <div className="shimmer h-5 w-16 rounded-full" />
        <div className="shimmer h-5 w-24 rounded-full" />
        <div className="shimmer h-5 w-20 rounded-full ml-auto" />
      </div>
      <div className="shimmer h-4 w-3/4 rounded" />
      <div className="shimmer h-3 w-full rounded" />
      <div className="shimmer h-3 w-5/6 rounded" />
      <div className="score-bar-track mt-2">
        <div className="shimmer score-bar-fill" style={{ width: "60%" }} />
      </div>
    </div>
  );
}

interface ResultCardProps {
  result: SearchResult;
  index: number;
  isActive: boolean;
  onClick: () => void;
}

function ResultCard({ result, index, isActive, onClick }: ResultCardProps) {
  const duration = result.end_time - result.start_time;

  return (
    <div
      onClick={onClick}
      className={`glass glass-hover rounded-2xl p-5 cursor-pointer fade-in-up ${
        isActive ? "glass-active" : ""
      }`}
      style={{ animationDelay: `${index * 60}ms`, animationFillMode: "both" }}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick()}
      aria-label={`Select result: ${result.video_id}`}
    >
      {/* Top row */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="badge badge-indigo">
            <Clock className="w-2.5 h-2.5" />
            {formatTime(result.start_time)}–{formatTime(result.end_time)}
          </span>
          <span className="badge badge-emerald">
            <Database className="w-2.5 h-2.5" />
            {result.dataset_source}
          </span>
          <span
            className={`badge ${
              result.score >= 0.7 ? "badge-emerald" : "badge-amber"
            }`}
          >
            <Zap className="w-2.5 h-2.5" />
            {(result.score * 100).toFixed(1)}%
          </span>
        </div>
        <span className="text-xs text-slate-500 font-mono shrink-0">
          #{index + 1}
        </span>
      </div>

      {/* Video ID */}
      <h3 className="text-sm font-semibold text-slate-200 font-mono mb-2 truncate">
        {result.video_id}
      </h3>

      {/* Explanation */}
      <p className="text-xs text-slate-400 leading-relaxed line-clamp-2 mb-3">
        <Sparkles className="w-3 h-3 inline mr-1 text-indigo-400" />
        {result.explanation}
      </p>

      {/* Context snippets */}
      {(result.transcript_text || result.ocr_text) && (
        <div className="space-y-1 border-t border-white/5 pt-2 mt-2">
          {result.transcript_text && (
            <div className="flex items-start gap-1.5 text-xs text-slate-500">
              <Volume2 className="w-3 h-3 mt-0.5 text-blue-400 shrink-0" />
              <span className="truncate italic">"{result.transcript_text}"</span>
            </div>
          )}
          {result.ocr_text && (
            <div className="flex items-start gap-1.5 text-xs text-slate-500">
              <FileText className="w-3 h-3 mt-0.5 text-amber-400 shrink-0" />
              <span className="truncate font-mono">{result.ocr_text}</span>
            </div>
          )}
        </div>
      )}

      {/* Score bar */}
      <div className="score-bar-track mt-3">
        <div
          className="score-bar-fill"
          style={{ width: `${result.score * 100}%` }}
        />
      </div>

      {/* Duration & play hint */}
      <div className="flex items-center justify-between mt-2">
        <span className="text-xs text-slate-600">
          {duration.toFixed(1)} s clip
        </span>
        <ChevronRight
          className={`w-3.5 h-3.5 transition-colors ${
            isActive ? "text-indigo-400" : "text-slate-600"
          }`}
        />
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function Home() {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [activeIdx, setActiveIdx] = useState<number | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [videoDuration, setVideoDuration] = useState(0);
  const [videoError, setVideoError] = useState(false);
  const [topK, setTopK] = useState(10);

  const videoRef = useRef<HTMLVideoElement>(null);
  const inputRef  = useRef<HTMLInputElement>(null);

  const activeResult = activeIdx !== null ? results[activeIdx] : null;

  // ── Search ────────────────────────────────────────────────────────────────

  const handleSearch = useCallback(async () => {
    const q = query.trim();
    if (!q || isLoading) return;

    setIsLoading(true);
    setError(null);
    setResults([]);
    setActiveIdx(null);
    setVideoError(false);

    try {
      const res = await fetch(`${API_URL}/api/v1/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, top_k: topK }),
      });

      if (!res.ok) {
        const errBody = await res.text();
        throw new Error(`API ${res.status}: ${errBody}`);
      }

      const data: SearchResponse = await res.json();
      setResults(data.results);

      // Auto-select first result
      if (data.results.length > 0) {
        setActiveIdx(0);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [query, topK, isLoading]);

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") handleSearch();
  };

  // ── Video player control ──────────────────────────────────────────────────

  const selectResult = useCallback((idx: number) => {
    setActiveIdx(idx);
    setVideoError(false);

    const result = results[idx];
    const vid = videoRef.current;
    if (!vid || !result) return;

    // Seek to start_time after source loads
    const seekAndPlay = () => {
      vid.currentTime = result.start_time;
      vid.play().catch(() => setIsPlaying(false));
    };

    if (vid.src && vid.readyState >= 1) {
      seekAndPlay();
    } else {
      vid.addEventListener("loadedmetadata", seekAndPlay, { once: true });
    }
  }, [results]);

  // When activeIdx changes, trigger selectResult
  useEffect(() => {
    if (activeIdx !== null && results[activeIdx]) {
      const vid = videoRef.current;
      if (!vid) return;
      const result = results[activeIdx];
      if (vid.readyState >= 1) {
        vid.currentTime = result.start_time;
        vid.play().catch(() => setIsPlaying(false));
      }
    }
  }, [activeIdx]); // eslint-disable-line react-hooks/exhaustive-deps

  // Track play/pause and time
  useEffect(() => {
    const vid = videoRef.current;
    if (!vid) return;
    const onPlay  = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    const onTime  = () => setCurrentTime(vid.currentTime);
    const onMeta  = () => setVideoDuration(vid.duration);
    vid.addEventListener("play", onPlay);
    vid.addEventListener("pause", onPause);
    vid.addEventListener("timeupdate", onTime);
    vid.addEventListener("loadedmetadata", onMeta);
    return () => {
      vid.removeEventListener("play", onPlay);
      vid.removeEventListener("pause", onPause);
      vid.removeEventListener("timeupdate", onTime);
      vid.removeEventListener("loadedmetadata", onMeta);
    };
  }, []);

  const togglePlay = () => {
    const vid = videoRef.current;
    if (!vid) return;
    vid.paused ? vid.play().catch(() => {}) : vid.pause();
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <>
      {/* Ambient background orbs */}
      <div className="bg-orbs" aria-hidden="true" />

      <div className="relative z-10 min-h-screen flex flex-col">
        {/* ── Header ──────────────────────────────────────────────────────── */}
        <header className="border-b border-white/5 bg-black/20 backdrop-blur-sm sticky top-0 z-20">
          <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
                <Layers className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="text-base font-bold text-slate-100 leading-none">
                  ChronoVision AI
                </h1>
                <p className="text-xs text-slate-500 mt-0.5">
                  ColQwen2 · MaxSim · Gemini
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Qdrant online
              </span>
              <span className="hidden sm:block">UCF-101 · MSVD · 2,399 clips</span>
            </div>
          </div>
        </header>

        {/* ── Main ────────────────────────────────────────────────────────── */}
        <main className="flex-1 max-w-screen-2xl mx-auto w-full px-6 py-8">

          {/* Search bar */}
          <div className="mb-8">
            <div className="relative flex gap-3">
              <div className="flex-1 relative">
                {isLoading ? (
                  <Loader2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-indigo-400 animate-spin" />
                ) : (
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                )}
                <input
                  id="search-input"
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Describe a video moment… e.g. "archery bullseye shot" or "cooking pasta""
                  className="search-input w-full rounded-2xl pl-12 pr-5 py-4 text-base text-slate-100 placeholder:text-slate-600"
                  autoFocus
                  autoComplete="off"
                  spellCheck={false}
                />
              </div>

              {/* top-k selector */}
              <select
                id="top-k-select"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="glass rounded-2xl px-4 py-4 text-sm text-slate-400 bg-transparent cursor-pointer focus:outline-none focus:border-indigo-500 border border-transparent"
              >
                {[5, 10, 20, 30].map((n) => (
                  <option key={n} value={n} className="bg-slate-900">
                    Top {n}
                  </option>
                ))}
              </select>

              <button
                id="search-btn"
                onClick={handleSearch}
                disabled={isLoading || !query.trim()}
                className={`px-8 py-4 rounded-2xl font-semibold text-sm transition-all duration-200 flex items-center gap-2
                  ${
                    isLoading || !query.trim()
                      ? "bg-slate-800 text-slate-600 cursor-not-allowed"
                      : "bg-gradient-to-r from-indigo-600 to-violet-600 text-white hover:from-indigo-500 hover:to-violet-500 shadow-lg shadow-indigo-500/25 active:scale-95 pulse-ring"
                  }`}
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Zap className="w-4 h-4" />
                )}
                Search
              </button>
            </div>

            {/* Query hint */}
            {results.length === 0 && !isLoading && !error && (
              <div className="mt-4 flex flex-wrap gap-2">
                {["archery bullseye", "swimming freestyle", "basketball dunk", "cooking stir fry"].map(
                  (hint) => (
                    <button
                      key={hint}
                      onClick={() => { setQuery(hint); setTimeout(handleSearch, 50); }}
                      className="text-xs px-3 py-1.5 rounded-full border border-white/10 text-slate-500 hover:border-indigo-500/50 hover:text-indigo-400 transition-all"
                    >
                      {hint}
                    </button>
                  )
                )}
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 glass rounded-2xl p-4 border-rose-500/30 flex items-start gap-3 text-rose-400">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-semibold">Search failed</p>
                <p className="text-xs text-rose-400/70 mt-0.5 font-mono">{error}</p>
              </div>
            </div>
          )}

          {/* Results grid */}
          {(isLoading || results.length > 0) && (
            <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">

              {/* Left: Result list */}
              <div className="xl:col-span-2 space-y-3 max-h-[78vh] overflow-y-auto pr-1">
                {/* Header */}
                <div className="flex items-center justify-between px-1 mb-4">
                  <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-widest">
                    {isLoading ? "Searching …" : `${results.length} scenes matched`}
                  </h2>
                  {!isLoading && results.length > 0 && (
                    <span className="text-xs text-slate-600">
                      Best: {(results[0]?.score * 100).toFixed(1)}%
                    </span>
                  )}
                </div>

                {isLoading
                  ? Array.from({ length: 4 }).map((_, i) => (
                      <SkeletonCard key={i} />
                    ))
                  : results.map((result, idx) => (
                      <ResultCard
                        key={`${result.video_id}-${idx}`}
                        result={result}
                        index={idx}
                        isActive={activeIdx === idx}
                        onClick={() => selectResult(idx)}
                      />
                    ))}
              </div>

              {/* Right: Video player + explanation */}
              <div className="xl:col-span-3 space-y-4 sticky top-24">

                {/* Video player panel */}
                <div className="glass rounded-2xl overflow-hidden">
                  {/* Video */}
                  <div className="relative bg-black aspect-video">
                    {activeResult ? (
                      <>
                        <video
                          id="result-video-player"
                          ref={videoRef}
                          key={activeResult.video_url}
                          src={activeResult.video_url}
                          className="w-full h-full object-contain"
                          onError={() => setVideoError(true)}
                          preload="metadata"
                          playsInline
                        />
                        {/* Overlay when video not available */}
                        {videoError && (
                          <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80">
                            <Film className="w-10 h-10 text-slate-600 mb-3" />
                            <p className="text-sm text-slate-500 text-center px-6">
                              Video file not available locally.
                            </p>
                            <p className="text-xs text-slate-600 mt-1 font-mono">
                              {activeResult.video_url}
                            </p>
                            <p className="text-xs text-slate-600 mt-3">
                              Copy videos to{" "}
                              <code className="text-indigo-400">apps/web/public/videos/</code>
                            </p>
                          </div>
                        )}
                        {/* Play overlay */}
                        {!isPlaying && !videoError && (
                          <button
                            id="video-play-overlay"
                            onClick={togglePlay}
                            className="absolute inset-0 flex items-center justify-center group"
                            aria-label="Play video"
                          >
                            <div className="w-16 h-16 rounded-full bg-black/60 backdrop-blur flex items-center justify-center group-hover:scale-110 transition-transform border border-white/10">
                              <Play className="w-7 h-7 text-white fill-white ml-1" />
                            </div>
                          </button>
                        )}
                      </>
                    ) : (
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <Film className="w-12 h-12 text-slate-700 mb-3" />
                        <p className="text-sm text-slate-600">
                          Select a result to preview
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Controls */}
                  {activeResult && !videoError && (
                    <div className="px-5 py-4 border-t border-white/5 space-y-3">
                      {/* Progress bar */}
                      <div className="relative">
                        <div
                          className="w-full h-1 bg-slate-800 rounded-full cursor-pointer overflow-hidden"
                          onClick={(e) => {
                            const vid = videoRef.current;
                            if (!vid || !videoDuration) return;
                            const rect = e.currentTarget.getBoundingClientRect();
                            const x = e.clientX - rect.left;
                            vid.currentTime = (x / rect.width) * videoDuration;
                          }}
                        >
                          {/* Scene range highlight */}
                          {videoDuration > 0 && (
                            <div
                              className="absolute h-full bg-indigo-500/20 rounded-full"
                              style={{
                                left: `${(activeResult.start_time / videoDuration) * 100}%`,
                                width: `${((activeResult.end_time - activeResult.start_time) / videoDuration) * 100}%`,
                              }}
                            />
                          )}
                          {/* Playhead */}
                          {videoDuration > 0 && (
                            <div
                              className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full transition-all duration-100"
                              style={{ width: `${(currentTime / videoDuration) * 100}%` }}
                            />
                          )}
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <button
                            id="video-play-pause-btn"
                            onClick={togglePlay}
                            className="w-8 h-8 rounded-full bg-indigo-600 hover:bg-indigo-500 flex items-center justify-center transition-colors"
                            aria-label={isPlaying ? "Pause" : "Play"}
                          >
                            {isPlaying
                              ? <Pause className="w-3.5 h-3.5 text-white" />
                              : <Play className="w-3.5 h-3.5 text-white fill-white ml-0.5" />
                            }
                          </button>
                          <span className="text-xs text-slate-500 font-mono">
                            {formatTime(currentTime)} / {formatTime(videoDuration)}
                          </span>
                        </div>
                        <button
                          id="video-seek-start-btn"
                          onClick={() => {
                            const vid = videoRef.current;
                            if (vid && activeResult) {
                              vid.currentTime = activeResult.start_time;
                              vid.play().catch(() => {});
                            }
                          }}
                          className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
                        >
                          <Clock className="w-3 h-3" />
                          Jump to {formatTime(activeResult.start_time)}
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Explanation panel */}
                {activeResult && (
                  <div className="glass rounded-2xl p-5 space-y-4 fade-in-up">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-indigo-400" />
                      <h3 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                        AI Explanation
                      </h3>
                    </div>

                    <p className="text-sm text-slate-300 leading-relaxed">
                      {activeResult.explanation}
                    </p>

                    {/* Metadata grid */}
                    <div className="grid grid-cols-2 gap-3 pt-3 border-t border-white/5">
                      <div>
                        <p className="text-xs text-slate-600 mb-1">Video ID</p>
                        <p className="text-xs text-slate-300 font-mono truncate">
                          {activeResult.video_id}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-600 mb-1">Dataset</p>
                        <p className="text-xs text-slate-300">{activeResult.dataset_source}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-600 mb-1">Timestamp</p>
                        <p className="text-xs text-slate-300">
                          {activeResult.start_time.toFixed(1)} s → {activeResult.end_time.toFixed(1)} s
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-600 mb-1">MaxSim Score</p>
                        <p className={`text-xs font-bold ${scoreColor(activeResult.score)}`}>
                          {(activeResult.score * 100).toFixed(2)}%
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Empty state */}
          {!isLoading && results.length === 0 && !error && (
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500/10 to-violet-500/10 border border-indigo-500/20 flex items-center justify-center mb-6">
                <Search className="w-9 h-9 text-indigo-500/60" />
              </div>
              <h2 className="text-xl font-semibold text-slate-400 mb-2">
                Search 2,399 video moments
              </h2>
              <p className="text-sm text-slate-600 max-w-md">
                Powered by ColQwen2 late-interaction embeddings and Qdrant MaxSim —
                describe any visual moment in natural language.
              </p>
            </div>
          )}
        </main>
      </div>
    </>
  );
}
