/**
 * @file apps/web/src/components/LateInteractionHeatmap.tsx
 * @description ColPali Late-Interaction Patch-to-Token Heatmap Inspector & Radar Intensity Bar.
 * Renders an intensity bar directly above the progress slider showing where query tokens matched visual patches.
 */

"use client";

import React, { useState } from "react";
import { Sparkles, Eye, Info, CheckCircle2, Layers } from "lucide-react";
import { VideoItemMetadata } from "./SearchPlayground";

interface LateInteractionHeatmapProps {
  match: VideoItemMetadata;
  currentTime?: number;
  onSeek?: (seconds: number) => void;
}

export const LateInteractionHeatmap: React.FC<LateInteractionHeatmapProps> = ({
  match,
  currentTime,
  onSeek,
}) => {
  const [selectedTokenIdx, setSelectedTokenIdx] = useState<number>(0);
  const [showGridOverlay, setShowGridOverlay] = useState<boolean>(true);

  // Sample token scores for late-interaction inspection
  const tokenScores = [
    { token: "ColPali", bestPatch: 18, maxSim: 0.98 },
    { token: "late", bestPatch: 26, maxSim: 0.94 },
    { token: "interaction", bestPatch: 27, maxSim: 0.96 },
    { token: "MaxSim", bestPatch: 35, maxSim: 0.99 },
    { token: "formula", bestPatch: 36, maxSim: 0.92 },
  ];

  const currentToken = tokenScores[selectedTokenIdx] || tokenScores[0];

  // 64 values for 8x8 patch grid
  const patchHeatmap = [
    0.1, 0.1, 0.2, 0.2, 0.1, 0.1, 0.1, 0.1,
    0.2, 0.3, 0.4, 0.5, 0.3, 0.2, 0.1, 0.1,
    0.2, 0.5, 0.95, 0.98, 0.6, 0.3, 0.2, 0.1,
    0.1, 0.4, 0.92, 0.99, 0.88, 0.4, 0.2, 0.1,
    0.1, 0.3, 0.85, 0.91, 0.76, 0.3, 0.1, 0.1,
    0.1, 0.2, 0.4, 0.6, 0.5, 0.2, 0.1, 0.1,
    0.1, 0.1, 0.2, 0.3, 0.2, 0.1, 0.1, 0.1,
    0.0, 0.1, 0.1, 0.1, 0.1, 0.0, 0.0, 0.0,
  ];

  return (
    <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-4 sm:p-5 space-y-4 shadow-xl backdrop-blur-xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
            ColPali MaxSim Patch Heatmap
          </h3>
        </div>
        <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-indigo-950 text-indigo-300 border border-indigo-800">
          8×8 Patches (64 Vectors)
        </span>
      </div>

      <p className="text-xs text-slate-400 leading-relaxed">
        Click a query token below to inspect which 2D visual patches produced the highest cosine similarity alignment.
      </p>

      {/* Query Tokens Selection */}
      <div className="flex flex-wrap gap-2 pt-1">
        {tokenScores.map((t, idx) => {
          const isSelected = selectedTokenIdx === idx;
          return (
            <button
              key={idx}
              onClick={() => setSelectedTokenIdx(idx)}
              className={`px-3 py-1.5 rounded-xl text-xs font-mono flex items-center gap-1.5 transition-all ${
                isSelected
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30 ring-2 ring-indigo-400 scale-105"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white"
              }`}
            >
              <span className="font-semibold">{t.token}</span>
              <span className="text-[10px] opacity-80">
                {(t.maxSim * 100).toFixed(0)}%
              </span>
            </button>
          );
        })}
      </div>

      {/* ── Semantic Radar Intensity Bar directly above progress ── */}
      <div className="space-y-1 pt-1">
        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
          <span className="flex items-center gap-1 text-indigo-300 font-semibold">
            <Layers className="w-3 h-3" /> Token Match Intensity Radar:
          </span>
          <span className="text-emerald-400 font-bold">
            Peak: {(currentToken.maxSim * 100).toFixed(1)}% MaxSim @ Patch #{currentToken.bestPatch}
          </span>
        </div>

        <div className="h-4 w-full bg-slate-950 rounded-lg p-0.5 border border-slate-800 flex gap-0.5 overflow-hidden">
          {tokenScores.map((t, idx) => {
            const widthPct = 100 / tokenScores.length;
            const isCurrent = selectedTokenIdx === idx;
            return (
              <div
                key={idx}
                style={{ width: `${widthPct}%` }}
                onClick={() => {
                  setSelectedTokenIdx(idx);
                  if (onSeek) onSeek(match.start_time + idx * 3);
                }}
                title={`Token: ${t.token} | MaxSim: ${(t.maxSim * 100).toFixed(1)}%`}
                className={`h-full rounded-sm transition-all cursor-pointer ${
                  isCurrent
                    ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"
                    : t.maxSim >= 0.9
                    ? "bg-indigo-500 hover:bg-indigo-400"
                    : "bg-violet-600 hover:bg-violet-500"
                }`}
              />
            );
          })}
        </div>
      </div>

      {/* Visual Canvas with Heatmap Overlay */}
      <div className="relative aspect-video rounded-xl overflow-hidden border border-slate-800 bg-slate-950 flex items-center justify-center group shadow-inner">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-950 to-indigo-950/40 p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span className="bg-slate-900/80 px-2.5 py-1 rounded-full border border-slate-700">
              FRAME @ {match.start_time.toFixed(1)}s
            </span>
            <span className="bg-slate-900/80 px-2.5 py-1 rounded-full border border-slate-700 text-indigo-300">
              {match.category}
            </span>
          </div>

          <div className="text-center p-3 bg-slate-900/80 backdrop-blur rounded-xl border border-slate-800 max-w-md mx-auto">
            <p className="text-xs font-bold text-slate-100">
              {match.thumbnailPlaceholder || match.videoTitle}
            </p>
            <p className="text-[10px] text-slate-400 font-mono mt-1 line-clamp-1">
              {match.ocrText || "Token spatial projection active"}
            </p>
          </div>

          <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
            <span>Video: {match.videoId}</span>
            <span>ColPali v1.2 Late Interaction</span>
          </div>
        </div>

        {/* 8x8 Patch Grid Overlay */}
        {showGridOverlay && (
          <div className="absolute inset-0 grid grid-cols-8 grid-rows-8 gap-0.5 p-1 bg-black/40 pointer-events-none">
            {patchHeatmap.map((val, pIdx) => {
              const isBest = currentToken?.bestPatch === pIdx;
              const intensity = isBest ? 0.95 : Math.max(val * 0.7, 0.05);

              return (
                <div
                  key={pIdx}
                  style={{
                    backgroundColor: isBest
                      ? "rgba(239, 68, 68, 0.8)"
                      : `rgba(99, 102, 241, ${intensity})`,
                  }}
                  className={`relative flex items-center justify-center rounded-[2px] transition-all border ${
                    isBest
                      ? "border-amber-300 ring-2 ring-amber-400"
                      : "border-indigo-500/20"
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
      <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
        <div>
          <span className="text-slate-400">Token Target: </span>
          <span className="text-indigo-300 font-bold">&ldquo;{currentToken?.token}&rdquo;</span>
        </div>
        <div>
          <span className="text-slate-400">Best Patch: </span>
          <span className="text-amber-400 font-bold">#{currentToken?.bestPatch}</span>
        </div>
        <div>
          <span className="text-slate-400">Max Cosine Sim: </span>
          <span className="text-emerald-400 font-bold">
            {(currentToken?.maxSim * 100).toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  );
};
