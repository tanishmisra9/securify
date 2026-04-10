import { useCallback, useRef } from 'react';

import { useAppStore } from '../store/useAppStore';
import DocumentRenderer from './ui/DocumentRenderer';

export default function RedactedView() {
  const { doc } = useAppStore();
  if (!doc) return null;

  const originalRef = useRef<HTMLDivElement>(null);
  const redactedRef = useRef<HTMLDivElement>(null);
  const syncLockRef = useRef<'original' | 'redacted' | null>(null);

  const syncScroll = useCallback(
    (source: 'original' | 'redacted') => {
      if (syncLockRef.current && syncLockRef.current !== source) return;

      const sourceEl = source === 'original' ? originalRef.current : redactedRef.current;
      const targetEl = source === 'original' ? redactedRef.current : originalRef.current;
      if (!sourceEl || !targetEl) return;

      syncLockRef.current = source;
      targetEl.scrollTop = sourceEl.scrollTop;
      targetEl.scrollLeft = sourceEl.scrollLeft;

      requestAnimationFrame(() => {
        if (syncLockRef.current === source) {
          syncLockRef.current = null;
        }
      });
    },
    []
  );

  return (
    <div className="h-full min-h-0 flex flex-col px-8 py-6 gap-4 overflow-hidden">
      <div className="flex gap-5 flex-1 min-h-0 overflow-hidden">
        <div className="flex-1 flex flex-col min-w-0">
          <p className="section-label mb-2">Original document</p>
          <DocumentRenderer text={doc.original_text} scrollContainerRef={originalRef} onScroll={() => syncScroll('original')} />
        </div>

        <div className="flex-1 flex flex-col min-w-0">
          <p className="section-label mb-2">Redacted copy</p>
          <DocumentRenderer text={doc.redacted_text} redacted scrollContainerRef={redactedRef} onScroll={() => syncScroll('redacted')} />
        </div>
      </div>
    </div>
  );
}
