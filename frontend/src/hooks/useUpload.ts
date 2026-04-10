import { useCallback, useState } from 'react';

import { uploadDoc } from '../api/client';
import { useAppStore } from '../store/useAppStore';

export function useUpload() {
  const [error, setError] = useState<string | null>(null);
  const { setDoc, setLoading } = useAppStore();

  const uploadFile = useCallback(
    async (file: File | null) => {
      if (!file) return;
      setLoading(true, 'Scanning for PII…');
      setError(null);
      try {
        const result = await uploadDoc(file);
        setDoc(result);
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Upload failed';
        setError(msg);
        throw e;
      } finally {
        setLoading(false);
      }
    },
    [setDoc, setLoading]
  );

  return { uploadFile, error, clearError: () => setError(null) };
}
