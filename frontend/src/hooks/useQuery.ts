import { useCallback, useState } from 'react';

import { queryDoc } from '../api/client';
import { useAppStore } from '../store/useAppStore';

function uid() {
  return Math.random().toString(36).slice(2);
}

export function useQuery() {
  const [thinking, setThinking] = useState(false);
  const { doc, addMessage } = useAppStore();

  const sendQuery = useCallback(
    async (rawQuery: string) => {
      const query = rawQuery.trim();
      if (!query || !doc || thinking) return;

      addMessage({ id: uid(), role: 'user', content: query, timestamp: Date.now() });
      setThinking(true);

      try {
        const res = await queryDoc(query, doc.chunks, doc.entity_map);
        addMessage({
          id: uid(),
          role: 'assistant',
          content: res.answer,
          verdict: res.verdict,
          timestamp: Date.now(),
        });
      } catch {
        addMessage({
          id: uid(),
          role: 'assistant',
          content: 'Something went wrong. Please try again.',
          verdict: 'ERROR',
          timestamp: Date.now(),
        });
      } finally {
        setThinking(false);
      }
    },
    [addMessage, doc, thinking]
  );

  return { thinking, sendQuery };
}
