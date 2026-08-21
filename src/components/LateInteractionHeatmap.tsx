import React, { useState } from 'react';
import { VideoKeyframeMatch } from '../types';
import { Sparkles, Eye, Info, CheckCircle2 } from 'lucide-react';

interface LateInteractionHeatmapProps {
  match: VideoKeyframeMatch;
}

export const LateInteractionHeatmap: React.FC<LateInteractionHeatmapProps> = ({ match }) => {
  const [selectedTokenIdx, setSelectedTokenIdx] = useState<number>(0);
  const [showGridOverlay, setShowGridOverlay] = useState<boolean>(true);

  const currentToken = match.tokenScores[selectedTokenIdx] || match.tokenScores[0];

  return (
    <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-5 space-y-4 shadow-xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-semibold text-slate-100 uppercase tracking-wider">
            ColPali MaxSim Attention Map
          </h3>
        </div>
        <span className="px-2.5 py-0.5 rounded text-xs font-mono bg-indigo-950 text-indigo-300 border border-indigo-800">
          8x8 Patches (64 vectors)
        </span>
      </div>

      <p className="text-xs text-slate-400 leading-relaxed">
        Click a query token below to inspect which 2D visual patches in the video frame produced the highest cosine similarity alignment.
      </p>

      {/* Query Tokens Selection */}
      <div className="flex flex-wrap gap-2 pt-1">
        {match.tokenScores.map((t, idx) => {
          const isSelected = selectedTokenIdx === idx;
          return (
            <button
              key={idx}
              onClick={() => setSelectedTokenIdx(idx)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 transition-all ${
                isSelected
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 ring-2 ring-indigo-400'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              <span className="font-semibold">{t.token}</span>
              <span className="text-[10px] opacity-80">{(t.maxSim * 100).toFixed(0)}%</span>
            </button>
          );
        })}
      </div>

      {/* Visual Canvas with Heatmap Overlay */}
      <div className="relative aspect-video rounded-lg overflow-hidden border border-slate-800 bg-slate-950 flex items-center justify-center group">
        {/* Simulated Frame Canvas background */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-950 to-indigo-950/40 p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span className="bg-slate-900/80 px-2 py-0.5 rounded border border-slate-700">
              FRAME @ {match.timestampFormatted}
            </span>
            <span className="bg-slate-900/80 px-2 py-0.5 rounded border border-slate-700 text-indigo-300">
              {match.category}
            </span>
          </div>

          <div className="text-center p-3 bg-slate-900/70 backdrop-blur rounded border border-slate-800/80">
            <p className="text-xs font-semibold text-slate-200">{match.thumbnailPlaceholder}</p>
            <p className="text-[10px] text-slate-400 font-mono mt-1 line-clamp-1">
              {match.ocrExtractedText.split('\n')[0]}
            </p>
          </div>

          <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
            <span>Video: {match.videoId}</span>
            <span>ColPali v1.2</span>
          </div>
        </div>

        {/* 8x8 Patch Grid Overlay */}
        {showGridOverlay && (
          <div className="absolute inset-0 grid grid-cols-8 grid-rows-8 gap-0.5 p-1 bg-black/40 pointer-events-none">
            {match.patchHeatmap.map((val, pIdx) => {
              // Highlight the best patch specifically for this token or show distribution
              const isBest = currentToken?.bestPatch === pIdx;
              const intensity = isBest ? 0.95 : Math.max(val * 0.7, 0.05);

              return (
                <div
                  key={pIdx}
                  style={{
                    backgroundColor: isBest
                      ? 'rgba(239, 68, 68, 0.75)'
                      : `rgba(99, 102, 241, ${intensity})`
                  }}
                  className={`relative flex items-center justify-center rounded-[2px] transition-all border ${
                    isBest ? 'border-amber-300 ring-2 ring-amber-400' : 'border-indigo-500/20'
                  }`}
                >
                  {isBest && (
                    <span className="text-[9px] font-bold text-white font-mono drop-shadow">
                      MAX
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Stats footer */}
      <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between text-xs font-mono">
        <div>
          <span className="text-slate-400">Token Target: </span>
          <span className="text-indigo-300 font-bold">"{currentToken?.token}"</span>
        </div>
        <div>
          <span className="text-slate-400">Best Patch: </span>
          <span className="text-amber-400 font-bold">#{currentToken?.bestPatch}</span>
        </div>
        <div>
          <span className="text-slate-400">Max Cosine Sim: </span>
          <span className="text-emerald-400 font-bold">{currentToken?.maxSim}</span>
        </div>
      </div>
    </div>
  );
};
