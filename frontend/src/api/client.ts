import type { AuditRow, DocState } from '../types';

const BASE = '/api';

export async function uploadDoc(file: File): Promise<DocState> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? 'Upload failed');
  }
  return res.json();
}

export interface QueryResult {
  answer: string;
  verdict: string;
  injection_detected: boolean;
  pii_leak_detected: boolean;
}

export async function queryDoc(
  query: string,
  chunks: string[],
  entity_map: Record<string, string>
): Promise<QueryResult> {
  const res = await fetch(`${BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, chunks, entity_map }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? 'Query failed');
  }
  return res.json();
}

export async function fetchAudit(): Promise<AuditRow[]> {
  const res = await fetch(`${BASE}/audit`);
  if (!res.ok) throw new Error('Failed to fetch audit log');
  return res.json();
}

export interface FlagResult {
  redacted_text: string;
  entity_map: Record<string, string>;
  entity_counts: Record<string, number>;
  placeholder: string;
}

export async function flagEntity(
  text: string,
  label: string,
  original_text: string,
  redacted_text: string,
  entity_map: Record<string, string>,
  entity_counts: Record<string, number>
): Promise<FlagResult> {
  const res = await fetch('/api/flag', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text,
      label,
      original_text,
      redacted_text,
      entity_map,
      entity_counts,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? 'Flag failed');
  }
  return res.json();
}
