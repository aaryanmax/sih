import React, { useState } from 'react';
import { Folder, FolderOpen, FileCode, FileText, File, ChevronRight, ChevronDown, Copy, Check, Download, Layers } from 'lucide-react';
import { MonorepoNode } from '../types';

interface FileTreeViewerProps {
  tree: MonorepoNode;
  onSelectFile?: (node: MonorepoNode) => void;
  activePath?: string;
}

export const FileTreeViewer: React.FC<FileTreeViewerProps> = ({ tree, onSelectFile, activePath }) => {
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({
    'root': true,
    'github': true,
    'apps': true,
    'apps-web': true,
    'apps-api': true,
    'packages': true,
    'pkg-vllm': true,
    'pkg-late-interaction': true,
    'pkg-audio-ocr': true
  });

  const toggleFolder = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedFolders(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const renderNode = (node: MonorepoNode, depth: number = 0) => {
    const isFolder = node.type === 'folder';
    const isExpanded = expandedFolders[node.id];
    const isSelected = activePath === node.path;

    return (
      <div key={node.id} className="select-none text-xs font-mono">
        <div
          onClick={(e) => {
            if (isFolder) {
              toggleFolder(node.id, e);
            } else if (onSelectFile) {
              onSelectFile(node);
            }
          }}
          style={{ paddingLeft: `${depth * 14 + 8}px` }}
          className={`flex items-center gap-1.5 py-1 px-2 rounded cursor-pointer transition-colors ${
            isSelected
              ? 'bg-indigo-900/60 text-indigo-300 font-semibold border-l-2 border-indigo-500'
              : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
          }`}
        >
          {isFolder ? (
            <>
              <button
                type="button"
                onClick={(e) => toggleFolder(node.id, e)}
                className="text-slate-500 hover:text-slate-300 p-0.5"
              >
                {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              </button>
              {isExpanded ? (
                <FolderOpen className="w-4 h-4 text-indigo-400 shrink-0" />
              ) : (
                <Folder className="w-4 h-4 text-indigo-400 shrink-0" />
              )}
            </>
          ) : (
            <>
              <span className="w-3.5" />
              {node.name.endsWith('.py') ? (
                <FileCode className="w-4 h-4 text-emerald-400 shrink-0" />
              ) : node.name.endsWith('.tsx') || node.name.endsWith('.ts') ? (
                <FileCode className="w-4 h-4 text-sky-400 shrink-0" />
              ) : node.name.endsWith('.yml') || node.name.endsWith('.yaml') ? (
                <FileText className="w-4 h-4 text-amber-400 shrink-0" />
              ) : node.name === '.gitignore' ? (
                <File className="w-4 h-4 text-rose-400 shrink-0" />
              ) : (
                <File className="w-4 h-4 text-slate-400 shrink-0" />
              )}
            </>
          )}

          <span className="truncate">{node.name}</span>

          {node.milestone && (
            <span className="ml-auto px-1.5 py-0.2 rounded text-[10px] bg-indigo-950 text-indigo-300 border border-indigo-800/80">
              {node.milestone}
            </span>
          )}
        </div>

        {isFolder && isExpanded && node.children && (
          <div>{node.children.map(child => renderNode(child, depth + 1))}</div>
        )}
      </div>
    );
  };

  return <div className="space-y-0.5">{renderNode(tree)}</div>;
};

interface CodePreviewProps {
  file: MonorepoNode | null;
}

export const CodePreview: React.FC<CodePreviewProps> = ({ file }) => {
  const [copied, setCopied] = useState(false);

  if (!file || file.type === 'folder') {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-slate-500 bg-slate-950/60 rounded-xl border border-slate-800">
        <Layers className="w-10 h-10 mb-3 text-slate-600" />
        <p className="text-sm font-medium text-slate-400">Select any file from the Monorepo Tree</p>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          Browse M1 (vLLM), M2 (Late-Interaction), M3 (Audio/OCR), M4 (FastAPI), M5 (Next.js), and M6 (Docker Compose)
        </p>
      </div>
    );
  }

  const handleCopy = () => {
    if (file.content) {
      navigator.clipboard.writeText(file.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (!file.content) return;
    const blob = new Blob([file.content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = file.name;
    link.click();
    URL.revokeObjectURL(url);
  };

  const lines = (file.content || '').split('\n');

  return (
    <div className="bg-slate-950 rounded-xl border border-slate-800 flex flex-col h-full overflow-hidden shadow-2xl">
      {/* File Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-900/90 border-b border-slate-800 text-xs">
        <div className="flex items-center gap-2 text-slate-200">
          <FileCode className="w-4 h-4 text-indigo-400" />
          <span className="font-mono font-medium">{file.path}</span>
          {file.milestone && (
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-950 text-indigo-400 border border-indigo-800">
              Module {file.milestone}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Copy code"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Download file"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download</span>
          </button>
        </div>
      </div>

      {file.description && (
        <div className="px-4 py-2 bg-indigo-950/20 border-b border-indigo-900/40 text-xs text-indigo-300">
          <strong>Role:</strong> {file.description}
        </div>
      )}

      {/* Code Editor Body */}
      <div className="flex-1 overflow-auto p-4 font-mono text-xs text-slate-200 bg-slate-950">
        <table className="w-full border-collapse">
          <tbody>
            {lines.map((line, idx) => (
              <tr key={idx} className="hover:bg-slate-900/60">
                <td className="w-10 pr-4 text-right text-slate-600 select-none align-top font-mono text-[11px]">
                  {idx + 1}
                </td>
                <td className="whitespace-pre text-slate-200 font-mono select-text">{line || ' '}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
