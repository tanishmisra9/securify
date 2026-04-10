import { useCallback, useRef } from 'react';

import { AnimatePresence, motion } from 'framer-motion';
import { Activity, FileText, MessageSquare, RefreshCcw, Shield, Trash2, Upload } from 'lucide-react';

import { useUpload } from '../hooks/useUpload';
import { useAppStore } from '../store/useAppStore';
import type { View } from '../types';
import EntityBars from './ui/EntityBars';

const NAV: Array<{ key: View; label: string; icon: typeof MessageSquare }> = [
  { key: 'chat', label: 'Chat', icon: MessageSquare },
  { key: 'redacted', label: 'Redacted View', icon: FileText },
  { key: 'audit', label: 'Audit Log', icon: Activity },
];

export default function Sidebar() {
  const { doc, view, setView, clearDoc } = useAppStore();
  const { uploadFile, error, clearError } = useUpload();
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File | null) => {
      if (!file) return;
      try {
        await uploadFile(file);
      } catch {
        // handled by local error state
      } finally {
        if (fileRef.current) fileRef.current.value = '';
      }
    },
    [uploadFile]
  );

  return (
    <aside className="w-[260px] flex-shrink-0 bg-surface border-r border-border flex flex-col overflow-hidden">
      <div className="px-4 py-5 border-b border-border flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-[9px] bg-accent flex items-center justify-center shadow-lg shadow-accent/20 flex-shrink-0">
            <Shield size={15} className="text-white" strokeWidth={2.5} />
          </div>
          <div className="flex flex-col justify-center leading-tight">
            <span className="font-semibold text-[1rem] tracking-tight text-t1">Securify</span>
            <p className="text-t3 text-[0.68rem] -mt-0.5">PII-safe document intelligence</p>
          </div>
        </div>
      </div>

      <div className="px-4 pt-4 pb-2 flex-shrink-0">
        <p className="section-label mb-2">Document</p>
        <AnimatePresence mode="wait">
          {doc ? (
            <motion.div
              key="doc-loaded"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-surface2 border border-border rounded-[9px] px-3 py-2.5"
            >
              <p className="font-mono text-[0.73rem] text-t1 truncate">{doc.filename}</p>
              <p className="text-t3 text-[0.68rem] mt-0.5">{doc.total_entities} entities redacted</p>
            </motion.div>
          ) : (
            <motion.div
              key="doc-empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="border border-dashed border-border2 rounded-[9px] px-3 py-3 text-center text-t3 text-[0.75rem]"
            >
              No document loaded
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {doc && (
          <motion.div
            key="entity-bars"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="px-4 pb-2 overflow-hidden flex-shrink-0"
          >
            <p className="section-label mb-2 mt-3">Entities</p>
            <EntityBars counts={doc.entity_counts} confidences={doc.entity_confidences} />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="px-4 py-2 flex-shrink-0">
        <p className="section-label mb-2">Views</p>
        <nav className="flex flex-col gap-1">
          {NAV.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setView(key)}
              disabled={!doc && key !== 'chat'}
              className={[
                'flex items-center gap-2.5 w-full px-3 py-2 rounded-[8px] text-left text-[0.82rem] font-sans transition-all duration-150 disabled:opacity-30 disabled:cursor-not-allowed',
                view === key && doc
                  ? 'bg-surface2 border border-border2 text-accent'
                  : 'text-t2 hover:bg-surface2 hover:text-t1 border border-transparent',
              ].join(' ')}
            >
              <Icon size={14} strokeWidth={1.75} />
              {label}
            </button>
          ))}
        </nav>
      </div>

      <div className="flex-1" />

      <div className="px-4 pb-5 flex-shrink-0">
        <p className="section-label mb-2">{doc ? 'Upload' : 'Getting Started'}</p>
        <div className="space-y-2">
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.txt"
            className="hidden"
            onChange={(e) => void handleFile(e.target.files?.[0] ?? null)}
          />
          <button
            onClick={() => fileRef.current?.click()}
            className="w-full flex items-center justify-center gap-2 rounded-[9px] border border-border2 bg-surface2 px-3 py-2 text-[0.78rem] text-t2 hover:text-t1 hover:border-accent transition-colors"
          >
            {doc ? <RefreshCcw size={13} /> : <Upload size={13} />}
            {doc ? 'Change document' : 'Choose a document'}
          </button>
          {doc && (
            <button
              onClick={() => {
                clearError();
                clearDoc();
              }}
              className="w-full flex items-center justify-center gap-2 rounded-[9px] border border-border2 bg-surface2 px-3 py-2 text-[0.78rem] text-t3 hover:text-danger hover:border-danger/60 transition-colors"
            >
              <Trash2 size={13} />
              Remove document
            </button>
          )}
          {!doc && (
            <p className="text-[0.68rem] text-t3 leading-relaxed">
              Use the main upload area to drag and drop files.
            </p>
          )}
        </div>
        {error && (
          <div className="mt-2 text-[0.72rem] text-danger flex items-start justify-between gap-2">
            <span>{error}</span>
            <button className="text-t3 hover:text-t1" onClick={clearError}>
              ×
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
