export type View = 'chat' | 'redacted' | 'audit';
export type EntityCountMap = Record<string, number>;

export interface DocState {
  filename: string;
  original_text: string;
  redacted_text: string;
  entity_counts: EntityCountMap;
  entity_confidences: Record<string, number>;
  entity_map: Record<string, string>;
  chunks: string[];
  total_entities: number;
  suggested_questions: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  verdict?: string;
  timestamp: number;
}

export interface AuditRow {
  id: number;
  timestamp: string;
  query: string;
  entity_types: string[];
  verdict: string;
  pii_in_answer: boolean;
  injection_attempt: boolean;
}
