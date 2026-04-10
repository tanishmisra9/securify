import type { ReactNode, Ref, UIEventHandler } from 'react';

interface Props {
  text: string;
  redacted?: boolean;
  scrollContainerRef?: Ref<HTMLDivElement>;
  onScroll?: UIEventHandler<HTMLDivElement>;
}

const KEY_VALUE_RE = /^([A-Za-z][A-Za-z0-9\s()\/.'-]{1,40}):\s*(.*)$/;
const PLACEHOLDER_RE = /\[([A-Z_]+)_(\d+)\]/g;

export default function DocumentRenderer({
  text,
  redacted = false,
  scrollContainerRef,
  onScroll,
}: Props) {
  const lines = text.split('\n');

  return (
    <div
      ref={scrollContainerRef}
      onScroll={onScroll}
      className="flex-1 min-h-0 overflow-y-auto rounded-xl border border-border bg-surface p-6 shadow-[0_16px_60px_rgba(0,0,0,0.35)]"
    >
      <div className="mx-auto max-w-[780px] rounded-lg border border-border2/60 bg-[#f8fafc] text-slate-900 px-6 py-7">
        {lines.map((line, idx) => renderLine(line, idx, redacted))}
      </div>
    </div>
  );
}

function renderLine(line: string, idx: number, redacted: boolean) {
  const trimmed = line.trim();

  if (trimmed.length === 0) {
    return <div key={`sp-${idx}`} className="h-3" />;
  }

  const keyValueMatch = line.match(KEY_VALUE_RE);
  if (keyValueMatch) {
    const [, label, value] = keyValueMatch;
    return (
      <div key={`kv-${idx}`} className="grid grid-cols-[190px_1fr] gap-4 py-1.5 border-b border-slate-200/80 last:border-b-0">
        <div className="text-[0.72rem] uppercase tracking-[0.08em] text-slate-500 font-semibold">{label}</div>
        <div className="text-[0.86rem] leading-relaxed text-slate-900 break-words">{renderInline(value, redacted)}</div>
      </div>
    );
  }

  if (isHeadingLine(trimmed)) {
    return (
      <h4 key={`hd-${idx}`} className="text-[0.88rem] font-semibold tracking-[0.03em] text-slate-800 mt-4 mb-2 first:mt-0">
        {renderInline(trimmed, redacted)}
      </h4>
    );
  }

  return (
    <p key={`p-${idx}`} className="text-[0.86rem] leading-relaxed text-slate-800 whitespace-pre-wrap break-words mb-1.5">
      {renderInline(line, redacted)}
    </p>
  );
}

function isHeadingLine(text: string): boolean {
  if (text.includes(':') || text.length > 72) return false;
  const alphaOnly = text.replace(/[^A-Za-z]/g, '');
  if (alphaOnly.length < 3) return false;
  const isUpperish = text === text.toUpperCase() || /^\[SYNTHETIC DEMO FILE/.test(text);
  return isUpperish;
}

function renderInline(text: string, redacted: boolean): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;
  let match: RegExpExecArray | null;

  PLACEHOLDER_RE.lastIndex = 0;
  while ((match = PLACEHOLDER_RE.exec(text)) !== null) {
    const [raw] = match;
    const start = match.index;

    if (start > last) out.push(text.slice(last, start));

    if (redacted) {
      const widthCh = Math.max(4, Math.min(16, Math.round(raw.length * 0.65)));
      out.push(
        <span
          key={`ph-${start}`}
          className="inline-block align-middle rounded-[3px] bg-black border border-neutral-800 h-[1.05em]"
          style={{ width: `${widthCh}ch` }}
          aria-label="Redacted entity"
        />
      );
    } else {
      out.push(raw);
    }

    last = start + raw.length;
  }

  if (last < text.length) out.push(text.slice(last));
  return out;
}
