import { useMemo } from 'react';

import { useAppStore } from '../store/useAppStore';
import PiiChip from './ui/PiiChip';

export default function RedactedView() {
  const { doc } = useAppStore();
  if (!doc) return null;

  const highlightedRedacted = useMemo(() => highlightChips(doc.redacted_text), [doc.redacted_text]);

  return (
    <div className="h-full flex flex-col px-8 py-6 gap-4">
      <div className="flex gap-5 flex-1 min-h-0">
        <div className="flex-1 flex flex-col min-w-0">
          <p className="section-label mb-2">Original document</p>
          <div className="flex-1 bg-surface border border-border rounded-xl p-5 font-mono text-[0.79rem] leading-relaxed text-t2 overflow-y-auto whitespace-pre-wrap break-words min-h-0">
            {doc.original_text}
          </div>
        </div>

        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex items-center justify-between mb-2">
            <p className="section-label">Redacted copy</p>
            <span className="text-[0.65rem] text-t3 font-sans">entities never sent to LLM</span>
          </div>
          <div className="text-[0.68rem] text-t3 mb-2 flex items-center gap-2">
            <PiiChip label="PERSON" index={1} />
            <span>= redacted entity</span>
          </div>
          <div
            className="flex-1 bg-surface border border-border rounded-xl p-5 font-mono text-[0.79rem] leading-relaxed text-t2 overflow-y-auto whitespace-pre-wrap break-words min-h-0"
            dangerouslySetInnerHTML={{ __html: highlightedRedacted }}
          />
        </div>
      </div>
    </div>
  );
}

function highlightChips(text: string): string {
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>');

  return escaped.replace(
    /\[([A-Z_]+)_(\d+)\]/g,
    (_, label, idx) =>
      `<span style="display:inline;background:#0f2444;color:#93c5fd;border:1px solid #1d4ed8;border-radius:4px;padding:1px 5px;font-size:0.8em;font-weight:500">[${label}_${idx}]</span>`
  );
}
