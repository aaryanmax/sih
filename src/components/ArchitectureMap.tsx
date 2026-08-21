import React from 'react';
import { modulesData } from '../data/monorepoFiles';
import { ArchitectureModule } from '../types';
import { Cpu, Layers, Mic, Server, Layout, Container, ArrowRight, CheckCircle2, Terminal } from 'lucide-react';

interface ArchitectureMapProps {
  onSelectModule?: (mod: ArchitectureModule) => void;
  selectedModuleId?: string;
}

export const ArchitectureMap: React.FC<ArchitectureMapProps> = ({ onSelectModule, selectedModuleId }) => {
  const getIcon = (code: string) => {
    switch (code) {
      case 'M1': return <Cpu className="w-5 h-5 text-purple-400" />;
      case 'M2': return <Layers className="w-5 h-5 text-indigo-400" />;
      case 'M3': return <Mic className="w-5 h-5 text-sky-400" />;
      case 'M4': return <Server className="w-5 h-5 text-emerald-400" />;
      case 'M5': return <Layout className="w-5 h-5 text-amber-400" />;
      case 'M6': return <Container className="w-5 h-5 text-rose-400" />;
      default: return <Cpu className="w-5 h-5" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Visual Pipeline Flow Header */}
      <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Terminal className="w-5 h-5 text-indigo-400" />
              Multi-Modal Video Ingestion & Search Pipeline (M1 - M6)
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              End-to-end dataflow from raw video ingestion to real-time late-interaction retrieval
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 bg-emerald-950/60 px-3 py-1.5 rounded-lg border border-emerald-800">
            <CheckCircle2 className="w-4 h-4" />
            <span>Monorepo Architecture Synchronized</span>
          </div>
        </div>

        {/* Pipeline Diagram Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
          {modulesData.map((mod, idx) => {
            const isSelected = selectedModuleId === mod.id;
            return (
              <div
                key={mod.id}
                onClick={() => onSelectModule && onSelectModule(mod)}
                className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between ${
                  isSelected
                    ? 'bg-indigo-950/50 border-indigo-500 ring-2 ring-indigo-500 shadow-lg'
                    : 'bg-slate-950/80 border-slate-800 hover:border-slate-700 hover:bg-slate-900/50'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-slate-800 text-indigo-300">
                      {mod.code}
                    </span>
                    {getIcon(mod.code)}
                  </div>
                  <h4 className="text-xs font-bold text-slate-200 mt-2 line-clamp-2">
                    {mod.name.replace(/\(.*?\)/, '')}
                  </h4>
                  <p className="text-[11px] text-slate-400 font-mono mt-1 truncate">
                    {mod.path}
                  </p>
                </div>

                <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-500">
                  <span>{mod.techStack[0]}</span>
                  <span className="text-emerald-400">{mod.status}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Deep-Dive Module Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {modulesData.map((mod) => (
          <div
            key={mod.id}
            onClick={() => onSelectModule && onSelectModule(mod)}
            className="p-5 bg-slate-900/80 rounded-xl border border-slate-800 hover:border-slate-700 transition-all space-y-3 cursor-pointer"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <span className="p-1.5 bg-slate-800 rounded-lg">{getIcon(mod.code)}</span>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-mono font-bold text-indigo-400">{mod.code}</span>
                    <span className="text-xs text-slate-500">&bull;</span>
                    <span className="text-xs font-mono text-slate-400 truncate">{mod.path}</span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-100 mt-0.5">{mod.name}</h3>
                </div>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">{mod.role}</p>

            <div className="space-y-1.5 pt-2 border-t border-slate-800/80 text-xs">
              <div>
                <span className="text-slate-500 font-medium">Tech Stack: </span>
                <span className="text-slate-300 font-mono text-[11px]">
                  {mod.techStack.join(', ')}
                </span>
              </div>
              <div>
                <span className="text-slate-500 font-medium">Key Files: </span>
                <span className="text-indigo-300 font-mono text-[11px]">
                  {mod.keyFiles.join(', ')}
                </span>
              </div>
              <div className="bg-slate-950 p-2 rounded text-[11px] font-mono text-slate-400 space-y-1 mt-2">
                <div><span className="text-slate-500">IN:</span> {mod.inputs}</div>
                <div><span className="text-emerald-400">OUT:</span> {mod.outputs}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
