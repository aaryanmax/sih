/**
 * @file apps/web/src/app/page.tsx
 * @description ChronoVision AI - Next-gen Multimodal Video Intelligence Hub.
 * Features:
 *  - Phase 1 & 2: Smart Journey Player with vertical "Step 1 → Step 2 → Step 3" progress stepper,
 *    Auto-Advancing continuous player, and Anti-Cliffhanger auto-stitch.
 *  - Interactive Search Playground with Semantic Radar and Gemini 3.5 Flash-Lite explainability.
 */

"use client";

import React, { useState } from "react";
import {
  Layers,
  Database,
  Cpu,
  Sparkles,
  Zap,
  ShieldCheck,
  Radio,
  GraduationCap,
  Search,
} from "lucide-react";
import { SearchPlayground } from "../components/SearchPlayground";
import { SmartJourneyPlayer } from "../components/SmartJourneyPlayer";

export default function Home() {
  const [activeView, setActiveView] = useState<"journey" | "search">("journey");

  return (
    <>
      {/* Ambient background orbs for deep OLED contrast */}
      <div className="bg-orbs" aria-hidden="true" />

      <div className="relative z-10 min-h-screen flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
        {/* ── 2026 Android Expressive Sticky Top Header ──────────────────── */}
        <header className="sticky top-0 z-50 border-b border-white/5 bg-slate-950/80 backdrop-blur-xl">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            {/* Brand Logo & Title */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-500 via-violet-600 to-purple-600 p-0.5 shadow-lg shadow-indigo-500/25 flex items-center justify-center">
                <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
                  <Layers className="w-5 h-5 text-indigo-400" />
                </div>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-base font-bold text-slate-100 leading-tight flex items-center gap-1">
                    ChronoVision <span className="text-indigo-400 font-mono text-sm">AI</span>
                  </h1>
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 rounded-full">
                    ColPali MaxSim
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 hidden sm:block">
                  Autonomous Knowledge & Skill Styler &bull; Smart Video Intelligence
                </p>
              </div>
            </div>

            {/* Navigation View Switcher (Material 3 Segmented Control) */}
            <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-2xl border border-slate-800">
              <button
                onClick={() => setActiveView("journey")}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  activeView === "journey"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <GraduationCap className="w-3.5 h-3.5" />
                <span>Smart Journey</span>
              </button>

              <button
                onClick={() => setActiveView("search")}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  activeView === "search"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Search className="w-3.5 h-3.5" />
                <span>Search Radar</span>
              </button>

              <a
                href="/reels"
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 transition-all border border-transparent hover:border-slate-800"
              >
                <Radio className="w-3.5 h-3.5" />
                <span>Mobile Reels</span>
              </a>
            </div>

            {/* Live System Status Badges */}
            <div className="hidden lg:flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-950/60 border border-emerald-800/80 text-emerald-400 text-xs font-mono">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="font-semibold">Offline Demo Locked</span>
              </div>
            </div>
          </div>
        </header>

        {/* ── Main Content Container ─────────────────────────────────────── */}
        <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6">
          {/* Quick Metrics Bar (Tonal 2026 Material 3 Surfaces) */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-3.5 flex items-center justify-between backdrop-blur-md">
              <div>
                <div className="text-slate-400 text-[11px] font-semibold uppercase tracking-wider">
                  Retrieval Engine
                </div>
                <div className="text-slate-100 font-bold text-sm mt-0.5">
                  ColPali MaxSim
                </div>
              </div>
              <Layers className="w-5 h-5 text-indigo-400 shrink-0" />
            </div>

            <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-3.5 flex items-center justify-between backdrop-blur-md">
              <div>
                <div className="text-slate-400 text-[11px] font-semibold uppercase tracking-wider">
                  Reasoning Model
                </div>
                <div className="text-slate-100 font-bold text-sm mt-0.5">
                  Qwen2-VL-7B
                </div>
              </div>
              <Cpu className="w-5 h-5 text-violet-400 shrink-0" />
            </div>

            <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-3.5 flex items-center justify-between backdrop-blur-md">
              <div>
                <div className="text-slate-400 text-[11px] font-semibold uppercase tracking-wider">
                  Vector Database
                </div>
                <div className="text-slate-100 font-bold text-sm mt-0.5">
                  Qdrant Native MaxSim
                </div>
              </div>
              <Database className="w-5 h-5 text-rose-400 shrink-0" />
            </div>

            <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-3.5 flex items-center justify-between backdrop-blur-md">
              <div>
                <div className="text-slate-400 text-[11px] font-semibold uppercase tracking-wider">
                  Explainability
                </div>
                <div className="text-slate-100 font-bold text-sm mt-0.5">
                  Gemini 3.5 Flash-Lite
                </div>
              </div>
              <Sparkles className="w-5 h-5 text-amber-400 shrink-0" />
            </div>
          </div>

          {/* Dynamic View: Smart Journey Player vs Search Playground */}
          {activeView === "journey" ? (
            <SmartJourneyPlayer />
          ) : (
            <SearchPlayground />
          )}
        </main>

        {/* ── Footer ─────────────────────────────────────────────────────── */}
        <footer className="border-t border-slate-900 bg-slate-950/90 py-5 mt-10 backdrop-blur-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
            <div>
              ChronoVision AI &bull; Smart India Hackathon (SIH) Autonomous Knowledge & Skill Styler
            </div>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1 text-slate-400">
                <Zap className="w-3.5 h-3.5 text-indigo-400" />
                <span>MaxSim Continuous Pipeline</span>
              </span>
              <span className="flex items-center gap-1 text-slate-400">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Offline Demo Ready</span>
              </span>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
