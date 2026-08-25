"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { Play, Search, UploadCloud, ChevronUp, ChevronDown, Activity, ScanFace, MessageSquare, WholeWord } from "lucide-react";

export interface ReelResult {
  id: string;
  videoId: string;
  videoTitle: string;
  videoUrl: string;
  datasetSource: string;
  timestampSeconds: number;
  timestampFormatted: string;
  score: number;
  visual_score: number;
  whisper_score: number;
  ocr_score: number;
  rationale: string;
}

export const ReelPlayer: React.FC = () => {
  const [ingestUrl, setIngestUrl] = useState("");
  const [isIngesting, setIsIngesting] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<ReelResult[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [videoError, setVideoError] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  
  // Touch handlers for swiping
  const touchStartY = useRef<number>(0);
  
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartY.current = e.touches[0].clientY;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    const touchEndY = e.changedTouches[0].clientY;
    const diff = touchStartY.current - touchEndY;
    
    // Swipe Up (Next)
    if (diff > 50 && currentIndex < results.length - 1) {
      setCurrentIndex(prev => prev + 1);
    }
    // Swipe Down (Prev)
    if (diff < -50 && currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
    }
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (document.activeElement?.tagName === "INPUT") return;
      if (e.key === "ArrowDown" && currentIndex < results.length - 1) {
        setCurrentIndex(prev => prev + 1);
      } else if (e.key === "ArrowUp" && currentIndex > 0) {
        setCurrentIndex(prev => prev - 1);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentIndex, results.length]);

  const handleIngest = async () => {
    if (!ingestUrl.trim()) return;
    setIsIngesting(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/ingest/url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: ingestUrl }),
      });
      const data = await res.json();
      if (data.status === "success") {
        if (data.cached) {
          alert("⚡ Video is already downloaded & indexed! You can search its moments right away.");
        } else {
          alert("✅ Video successfully downloaded and AI moments indexed! You can now search for it.");
        }
        setIngestUrl("");
      } else {
        alert("Ingestion failed: " + JSON.stringify(data));
      }
    } catch (err: any) {
      console.error(err);
      alert("Error ingesting URL: " + (err.message || String(err)));
    } finally {
      setIsIngesting(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    setVideoError(false);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery, top_k: 5 }),
      });
      const data = await res.json();
      if (data.results && data.results.length > 0) {
        const formatTime = (secs: number) => {
          const m = Math.floor(secs / 60);
          const s = Math.floor(secs % 60);
          return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
        };

        const mapped: ReelResult[] = data.results.map((item: any, idx: number) => {
          const startTime = Number(item.start_time) || 0;
          const endTime = Number(item.end_time) || startTime + 2.0;
          return {
            id: `reel_${item.video_id}_${idx}`,
            videoId: item.video_id,
            videoTitle: item.video_filename || item.video_id,
            videoUrl: item.video_url || `/videos/shorts/${item.video_filename || item.video_id}`,
            datasetSource: item.dataset_source || "Live Ingest",
            timestampSeconds: startTime,
            timestampFormatted: `${formatTime(startTime)} - ${formatTime(endTime)}`,
            score: Number(item.score) || 0,
            visual_score: item.visual_score ?? 0.85,
            whisper_score: item.whisper_score ?? 0.7,
            ocr_score: item.ocr_score ?? 0.3,
            rationale: item.explanation || item.rationale || "Visual alignment detected",
          };
        });

        setResults(mapped);
        setCurrentIndex(0);
      } else {
        alert("No results found.");
      }
    } catch (err) {
      console.error(err);
      alert("Error searching");
    } finally {
      setIsSearching(false);
    }
  };

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
        setIsPlaying(false);
      } else {
        videoRef.current.play().then(() => {
          setIsPlaying(true);
        }).catch(() => {
          setIsPlaying(false);
        });
      }
    }
  };

  const currentResult = results[currentIndex];

  // When result index changes, reset error state
  useEffect(() => {
    setVideoError(false);
    if (videoRef.current && currentResult) {
      const targetTime = currentResult.timestampSeconds || 0;
      
      const seekAndPlay = () => {
        if (videoRef.current) {
          videoRef.current.currentTime = targetTime;
          videoRef.current.play().then(() => {
            setIsPlaying(true);
          }).catch(() => {
            setIsPlaying(false);
          });
        }
      };

      // If metadata is already loaded for this video element
      if (videoRef.current.readyState >= 1) {
        seekAndPlay();
      } else {
        // Add event listener for when metadata loads
        const videoEl = videoRef.current;
        videoEl.addEventListener('loadedmetadata', seekAndPlay, { once: true });
        return () => {
          videoEl.removeEventListener('loadedmetadata', seekAndPlay);
        };
      }
    }
  }, [currentIndex, currentResult]);

  return (
    <div className="bg-black w-full min-h-[100dvh] flex items-center justify-center font-sans overflow-hidden">
      {/* 9:16 Mobile Container */}
      <div 
        className="w-full max-w-md h-[100dvh] bg-slate-900 relative flex flex-col shadow-2xl"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        
        {/* TOP: Ingestion & Search Bar */}
        <div className="absolute top-0 left-0 right-0 z-20 p-4 space-y-3 bg-gradient-to-b from-black/80 to-transparent pt-8">
          {/* Ingest Bar */}
          <div className="flex items-center gap-2">
            <input 
              type="text" 
              placeholder="Paste YouTube/Insta URL..." 
              className="flex-1 bg-white/10 border border-white/20 rounded-full px-4 py-2 text-sm text-white placeholder-white/50 focus:outline-none focus:border-indigo-400 backdrop-blur-md"
              value={ingestUrl}
              onChange={(e) => setIngestUrl(e.target.value)}
            />
            <button 
              onClick={handleIngest}
              disabled={isIngesting}
              className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white disabled:opacity-50"
            >
              {isIngesting ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <UploadCloud className="w-4 h-4" />}
            </button>
          </div>

          {/* Search Bar */}
          <div className="flex items-center gap-2">
            <input 
              type="text" 
              placeholder="Search (e.g. 'carburetor', 'ColPali lecture', 'drone')..." 
              className="flex-1 bg-white/10 border border-white/20 rounded-full px-4 py-2 text-sm text-white placeholder-white/50 focus:outline-none focus:border-emerald-400 backdrop-blur-md"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <button 
              onClick={handleSearch}
              disabled={isSearching}
              className="w-10 h-10 rounded-full bg-emerald-600 flex items-center justify-center text-white disabled:opacity-50"
            >
              {isSearching ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Search className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* MIDDLE: Video Player */}
        <div className="absolute inset-0 z-0 bg-black flex items-center justify-center" onClick={togglePlay}>
          {currentResult ? (
            <>
              <video
                ref={videoRef}
                key={currentResult.videoUrl}
                src={currentResult.videoUrl}
                className="w-full h-full object-cover"
                playsInline
                loop
                muted={false}
                onError={() => setVideoError(true)}
              />
              {videoError && (
                <div className="absolute inset-0 bg-slate-950/90 flex flex-col items-center justify-center p-6 text-center text-white/80 space-y-4 backdrop-blur-sm">
                  <Activity className="w-12 h-12 text-indigo-400 animate-pulse" />
                  <p className="font-semibold text-white text-base">Dataset Video ({currentResult.datasetSource})</p>
                  <p className="text-xs text-white/60 max-w-xs leading-relaxed">
                    Raw file <code className="bg-white/10 px-1.5 py-0.5 rounded text-indigo-300 font-mono text-[11px]">{currentResult.videoTitle}</code> is from the pre-indexed benchmark dataset (video not saved locally).
                  </p>

                  {results.length > 1 && (
                    <p className="text-xs text-emerald-400 font-medium pt-2">
                      Use the arrow buttons on the right to navigate results
                    </p>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="text-white/30 flex flex-col items-center">
              <Activity className="w-12 h-12 mb-4 animate-pulse opacity-50" />
              <p>Ingest a URL or search to play</p>
            </div>
          )}
          
          {!isPlaying && currentResult && !videoError && (
            <div className="absolute inset-0 bg-black/30 flex items-center justify-center backdrop-blur-sm transition-opacity pointer-events-none">
              <div className="w-20 h-20 rounded-full bg-white/20 flex items-center justify-center">
                <Play className="w-10 h-10 text-white fill-white ml-2" />
              </div>
            </div>
          )}
        </div>

        {/* BOTTOM: Glassmorphic Overlay (TikTok style) */}
        {currentResult && (
          <div className="absolute bottom-0 left-0 right-0 z-20 p-4 pb-8 bg-gradient-to-t from-black/90 via-black/50 to-transparent pointer-events-none">
            <div className="space-y-3 pointer-events-auto">
              
              {/* Title & Info */}
              <div>
                <div className="flex items-center justify-between">
                  <h2 className="text-white font-bold text-base drop-shadow-md line-clamp-1">{currentResult.videoTitle}</h2>
                  <span className="text-xs font-mono text-white/50 bg-white/10 px-2 py-0.5 rounded-full">{currentIndex + 1} / {results.length}</span>
                </div>
                <p className="text-white/80 text-xs font-mono drop-shadow-md">
                  {currentResult.timestampFormatted} &bull; {(currentResult.score * 100).toFixed(1)}% Match
                </p>
              </div>

              {/* Explainability Rationale */}
              {currentResult.rationale && (
                <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-xl p-3 shadow-lg">
                  <p className="text-white text-sm leading-snug drop-shadow-sm">
                    {currentResult.rationale}
                  </p>
                </div>
              )}

              {/* Modality Scores */}
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg p-2 flex items-center gap-2">
                  <ScanFace className="w-3.5 h-3.5 text-indigo-400" />
                  <div className="flex-1">
                    <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${(currentResult.visual_score || 0) * 100}%` }} />
                    </div>
                  </div>
                </div>
                <div className="flex-1 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg p-2 flex items-center gap-2">
                  <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                  <div className="flex-1">
                    <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${(currentResult.whisper_score || 0) * 100}%` }} />
                    </div>
                  </div>
                </div>
                <div className="flex-1 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg p-2 flex items-center gap-2">
                  <WholeWord className="w-3.5 h-3.5 text-amber-400" />
                  <div className="flex-1">
                    <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                      <div className="h-full bg-amber-500 rounded-full" style={{ width: `${(currentResult.ocr_score || 0) * 100}%` }} />
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* Right Side Clickable Navigation Controls */}
        {results.length > 1 && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex flex-col gap-3 z-30">
            {currentIndex > 0 && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setCurrentIndex((prev) => prev - 1);
                }}
                className="w-10 h-10 rounded-full bg-black/70 border border-white/20 flex items-center justify-center text-white hover:bg-white/20 backdrop-blur-md shadow-xl transition-all active:scale-95"
                title="Previous Video"
              >
                <ChevronUp className="w-6 h-6" />
              </button>
            )}
            {currentIndex < results.length - 1 && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setCurrentIndex((prev) => prev + 1);
                }}
                className="w-10 h-10 rounded-full bg-black/70 border border-white/20 flex items-center justify-center text-white hover:bg-white/20 backdrop-blur-md shadow-xl transition-all active:scale-95"
                title="Next Video"
              >
                <ChevronDown className="w-6 h-6" />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
