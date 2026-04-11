import { useCallback, useState } from 'react';

import { uploadDoc } from '../api/client';
import { useAppStore } from '../store/useAppStore';

function buildSummary(counts: Record<string, number>): string {
  const parts: string[] = [];
  const map: Record<string, string> = {
    PERSON: 'name',
    SSN: 'SSN',
    MRN: 'medical record number',
    EMAIL: 'email',
    PHONE: 'phone number',
    ACCOUNT_NUM: 'account number',
    ORG: 'organization',
    GPE: 'location',
    DATE: 'date',
    DIAGNOSIS: 'diagnosis',
  };
  for (const [label, noun] of Object.entries(map)) {
    const n = counts[label];
    if (!n) continue;
    parts.push(`${n} ${noun}${n > 1 ? 's' : ''}`);
  }
  return parts.length ? parts.join(', ') : 'no PII detected';
}

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
        setDoc(result, buildSummary(result.entity_counts));
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
