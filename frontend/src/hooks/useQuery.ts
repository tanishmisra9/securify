import { useCallback, useState } from 'react';

import { queryDocStream } from '../api/client';
import { useAppStore } from '../store/useAppStore';

function uid() {
  return Math.random().toString(36).slice(2);
}

export function useQuery() {
  const [thinking, setThinking] = useState(false);
  const { doc, addMessage, updateLastMessage } = useAppStore();

  const sendQuery = useCallback(
    async (rawQuery: string) => {
      const query = rawQuery.trim();
      if (!query || !doc || thinking) return;

      addMessage({ id: uid(), role: 'user', content: query, timestamp: Date.now() });
      const placeholderId = uid();
      addMessage({
        id: placeholderId,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      });
      setThinking(true);

      try {
        let accumulated = '';
        await queryDocStream(
          query,
          doc.chunks,
          doc.entity_map,
          (token) => {
            accumulated += token;
            updateLastMessage({ content: accumulated });
          },
          (result) => {
            updateLastMessage({
              content: accumulated || result.answer,
              verdict: result.verdict,
            });
          }
        );
      } catch {
        updateLastMessage({
          content: 'Something went wrong. Please try again.',
          verdict: 'ERROR',
        });
      } finally {
        setThinking(false);
      }
    },
    [addMessage, doc, thinking, updateLastMessage]
  );

  return { thinking, sendQuery };
}
