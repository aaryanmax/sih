import React, { useState } from 'react';
import { 
  Video, 
  Layers, 
  Cpu, 
  FolderTree, 
  Search, 
  Activity, 
  Sparkles, 
  Database, 
  ShieldCheck, 
  Zap,
  ExternalLink,
  ChevronRight,
  Gauge
} from 'lucide-react';
import { SearchPlayground } from './components/SearchPlayground';
import { ArchitectureMap } from './components/ArchitectureMap';
import { FileTreeViewer } from './components/FileTreeViewer';
import { ArchitectureModule } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<'search' | 'architecture' | 'files'>('search');
  const [selectedModule, setSelectedModule] = useState<ArchitectureModule | null>(null);

  const handleSelectModule = (mod: ArchitectureModule) => {
    setSelectedModule(mod);
    setActiveTab('architecture');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-md border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-600 to-pink-500 p-0.5 shadow-lg shadow-indigo-500/20">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Video className="w-5 h-5 text-indigo-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-1.5">
                  ChronoVision <span className="text-indigo-400 font-mono text-sm">AI</span>
                </h1>
                <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 rounded-full">
                  ColPali MaxSim
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Deep Multimodal Semantic Video Intelligence & Retrieval Engine
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab('search')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'search'
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <Search className="w-3.5 h-3.5" />
              <span>Search Playground</span>
            </button>

            <button
              onClick={() => setActiveTab('architecture')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'architecture'
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>Architecture Pipeline</span>
            </button>

            <button
              onClick={() => setActiveTab('files')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'files'
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <FolderTree className="w-3.5 h-3.5" />
              <span>Monorepo Explorer</span>
            </button>
          </div>

          {/* Status & Metrics Badge */}
          <div className="hidden lg:flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-emerald-400 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Cluster Online</span>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Latency</div>
              <div className="text-xs font-mono text-slate-300 font-bold">18ms MaxSim</div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Quick Highlights Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5 flex items-center justify-between">
            <div>
              <div className="text-slate-400 text-xs font-medium">Late-Interaction Model</div>
              <div className="text-slate-100 font-bold text-sm mt-0.5">ColPali v1.2 Multi-Vector</div>
            </div>
            <Layers className="w-5 h-5 text-indigo-400 shrink-0" />
          </div>

          <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5 flex items-center justify-between">
            <div>
              <div className="text-slate-400 text-xs font-medium">Vision-Language Model</div>
              <div className="text-slate-100 font-bold text-sm mt-0.5">Qwen2-VL-7B (vLLM)</div>
            </div>
            <Cpu className="w-5 h-5 text-purple-400 shrink-0" />
          </div>

          <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5 flex items-center justify-between">
            <div>
              <div className="text-slate-400 text-xs font-medium">Vector Database</div>
              <div className="text-slate-100 font-bold text-sm mt-0.5">Qdrant MultiVectorConfig</div>
            </div>
            <Database className="w-5 h-5 text-rose-400 shrink-0" />
          </div>

          <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5 flex items-center justify-between">
            <div>
              <div className="text-slate-400 text-xs font-medium">Explainability Rationale</div>
              <div className="text-slate-100 font-bold text-sm mt-0.5">Gemini 3.5 Flash-Lite</div>
            </div>
            <Sparkles className="w-5 h-5 text-amber-400 shrink-0" />
          </div>
        </div>

        {/* Tab Views */}
        {activeTab === 'search' && <SearchPlayground />}
        {activeTab === 'architecture' && (
          <ArchitectureMap 
            onSelectModule={handleSelectModule} 
            selectedModuleId={selectedModule?.id} 
          />
        )}
        {activeTab === 'files' && <FileTreeViewer />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
          <div>
            ChronoVision AI &bull; Smart India Hackathon (SIH) Multimodal Video Intelligence
          </div>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1 text-slate-400">
              <Zap className="w-3.5 h-3.5 text-indigo-400" />
              <span>MaxSim Token Comparator</span>
            </span>
            <span className="flex items-center gap-1 text-slate-400">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Production Scaffold</span>
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
