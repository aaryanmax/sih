import React, { useState } from 'react';
import { Search, Sparkles, Video, Volume2, FileText, Play, Pause, RotateCcw, SlidersHorizontal, CheckCircle2, ChevronRight } from 'lucide-react';
import { sampleKeyframeMatches } from '../data/sampleVideos';
import { VideoKeyframeMatch } from '../types';
import { LateInteractionHeatmap } from './LateInteractionHeatmap';

export const SearchPlayground: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('ColPali late interaction MaxSim formula');
  const [selectedMatch, setSelectedMatch] = useState<VideoKeyframeMatch>(sampleKeyframeMatches[0]);
  const [activeTab, setActiveTab] = useState<'visual' | 'qwen' | 'ocr' | 'whisper'>('visual');
  const [filterModality, setFilterModality] = useState<string>('all');
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackTime, setPlaybackTime] = useState<number>(selectedMatch.timestampSeconds);

  const filteredMatches = sampleKeyframeMatches.filter(m => {
    if (filterModality === 'all') return true;
    return m.modality === filterModality;
  });

  const handleSelectMatch = (match: VideoKeyframeMatch) => {
    setSelectedMatch(match);
    setPlaybackTime(match.timestampSeconds);
  };

  return (
    <div className="space-y-6">
      {/* Search Input Bar */}
      <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-4 shadow-xl space-y-3">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search video timestamps by semantic visuals, spoken audio, or OCR..."
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-5 py-3.5 pl-12 text-slate-100 placeholder-slate-500 text-base focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 font-sans"
          />
          <Search className="w-5 h-5 text-slate-400 absolute left-4 top-4" />
        </div>

        {/* Quick query chips & Modality filter */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs pt-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-slate-500 font-medium">Try suggestions:</span>
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
                className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
              >
                {preset}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800">
            {['all', 'visual_patches', 'ocr_text', 'speech_audio'].map((mod) => (
              <button
                key={mod}
                onClick={() => setFilterModality(mod)}
                className={`px-2.5 py-1 rounded text-xs capitalize transition-colors ${
                  filterModality === mod
                    ? 'bg-indigo-600 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {mod.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Interactive Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Ranked Search Matches (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between px-1">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Ranked Keyframe Matches ({filteredMatches.length})
            </h3>
            <span className="text-xs text-indigo-400 font-mono">M2 Late-Interaction Ranked</span>
          </div>

          <div className="space-y-3">
            {filteredMatches.map((match) => {
              const isSelected = selectedMatch.id === match.id;
              return (
                <div
                  key={match.id}
                  onClick={() => handleSelectMatch(match)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-slate-900 border-indigo-500 ring-1 ring-indigo-500/50 shadow-lg shadow-indigo-500/10'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded font-mono text-xs font-semibold bg-indigo-950 text-indigo-300 border border-indigo-800">
                          {match.timestampFormatted}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[11px] bg-slate-800 text-slate-300 capitalize">
                          {match.modality.replace('_', ' ')}
                        </span>
                        <span className="text-xs text-emerald-400 font-mono font-semibold">
                          {(match.score * 100).toFixed(1)}% MaxSim
                        </span>
                      </div>
                      <h4 className="text-sm font-semibold text-slate-200 mt-2 line-clamp-1">
                        {match.videoTitle}
                      </h4>
                    </div>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectMatch(match);
                        setIsPlaying(true);
                      }}
                      className="p-2 rounded-lg bg-slate-800 hover:bg-indigo-600 text-slate-300 hover:text-white transition-colors shrink-0"
                    >
                      <Play className="w-4 h-4 fill-current" />
                    </button>
                  </div>

                  <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                    {match.ocrExtractedText.replace(/\n/g, ' ')}
                  </p>

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

        {/* Right Column: Video Synchronizer & Modality Inspector (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Synchronized Player Screen */}
          <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Video className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-semibold text-slate-100">
                  Synchronized Frame Player ({selectedMatch.timestampFormatted})
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">{selectedMatch.videoId}</span>
            </div>

            {/* Video Canvas Box */}
            <div className="aspect-video bg-slate-950 rounded-xl border border-slate-800 relative overflow-hidden flex flex-col justify-between p-4">
              <div className="flex items-center justify-between text-xs font-mono text-slate-300">
                <span className="bg-black/60 px-2.5 py-1 rounded backdrop-blur border border-white/10">
                  {selectedMatch.videoTitle}
                </span>
                <span className="bg-emerald-950/80 text-emerald-300 border border-emerald-800 px-2 py-1 rounded">
                  MaxSim: {(selectedMatch.score * 100).toFixed(1)}%
                </span>
              </div>

              <div className="text-center p-6 bg-slate-900/80 rounded-xl border border-slate-800 backdrop-blur max-w-lg mx-auto">
                <p className="text-sm font-semibold text-slate-100">{selectedMatch.thumbnailPlaceholder}</p>
                <p className="text-xs text-indigo-300 font-mono mt-2 bg-indigo-950/60 p-2 rounded border border-indigo-900/40">
                  Matched via {selectedMatch.modality.replace('_', ' ')} alignment
                </p>
              </div>

              {/* Player Timeline Controls */}
              <div className="bg-black/70 backdrop-blur rounded-lg p-2.5 flex flex-col gap-2 border border-white/10">
                {/* Visual Heatmap Overlay */}
                {selectedMatch.timelineHeatmap && (
                  <div className="relative h-6 flex items-end gap-[1px] group w-full px-10">
                    {selectedMatch.timelineHeatmap.map((pt, i) => {
                      const heightPct = Math.max(10, pt.score * 100);
                      return (
                        <div
                          key={i}
                          style={{ height: `${heightPct}%`, opacity: pt.score + 0.2 }}
                          className="flex-1 bg-indigo-500 rounded-t-[2px] transition-all hover:bg-indigo-400 cursor-pointer"
                          title={`Time: ${pt.timestamp}s | Score: ${(pt.score * 100).toFixed(0)}%`}
                          onClick={() => setPlaybackTime(pt.timestamp)}
                        />
                      );
                    })}
                  </div>
                )}
                
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="p-1.5 rounded-md bg-indigo-600 text-white hover:bg-indigo-500 shrink-0"
                  >
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
                  </button>
                  <span className="text-xs font-mono text-slate-300 w-10 text-right">{selectedMatch.timestampFormatted}</span>
                  <input
                    type="range"
                    min="0"
                    max="600"
                    value={playbackTime}
                    onChange={(e) => setPlaybackTime(Number(e.target.value))}
                    className="flex-1 accent-indigo-500 cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                  />
                  <span className="text-xs font-mono text-slate-400 w-10">10:00</span>
                </div>
              </div>
            </div>

            {/* Modality Inspection Tabs */}
            <div className="flex border-b border-slate-800 gap-2">
              <button
                onClick={() => setActiveTab('visual')}
                className={`pb-2 px-3 text-xs font-medium border-b-2 transition-colors ${
                  activeTab === 'visual'
                    ? 'border-indigo-500 text-indigo-400 font-semibold'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                M2 ColPali Heatmap
              </button>
              <button
                onClick={() => setActiveTab('qwen')}
                className={`pb-2 px-3 text-xs font-medium border-b-2 transition-colors ${
                  activeTab === 'qwen'
                    ? 'border-indigo-500 text-indigo-400 font-semibold'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                M1 Qwen2-VL Reasoning
              </button>
              <button
                onClick={() => setActiveTab('ocr')}
                className={`pb-2 px-3 text-xs font-medium border-b-2 transition-colors ${
                  activeTab === 'ocr'
                    ? 'border-indigo-500 text-indigo-400 font-semibold'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                M3 PaddleOCR Extracted
              </button>
              <button
                onClick={() => setActiveTab('whisper')}
                className={`pb-2 px-3 text-xs font-medium border-b-2 transition-colors ${
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
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
                <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold">
                  <Sparkles className="w-4 h-4" />
                  Qwen2-VL-7B Vision-Language CoT Reasoning (vLLM Engine)
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                  {selectedMatch.qwenReasoning}
                </p>
                <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
                  <span>Inference Latency: 42ms</span>
                  <span>vLLM Engine: Enabled</span>
                  <span>Model: Qwen2-VL-7B-Instruct</span>
                </div>
              </div>
            )}

            {activeTab === 'ocr' && (
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2 font-mono">
                <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold">
                  <FileText className="w-4 h-4" />
                  Keyframe OCR Bounding Box Text (PaddleOCR)
                </div>
                <pre className="p-3 bg-slate-900 rounded-lg text-xs text-slate-200 whitespace-pre-wrap border border-slate-800">
                  {selectedMatch.ocrExtractedText}
                </pre>
              </div>
            )}

            {activeTab === 'whisper' && (
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2 font-mono">
                <div className="flex items-center gap-2 text-sky-400 text-xs font-semibold">
                  <Volume2 className="w-4 h-4" />
                  Audio Speech Transcript (Faster-Whisper with Timestamps)
                </div>
                <p className="p-3 bg-slate-900 rounded-lg text-xs text-slate-200 italic border border-slate-800">
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
