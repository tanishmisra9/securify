import React from 'react';

import { PLACEHOLDER_RE } from './placeholderUtils';

interface Props {
  text: string;
}

export default function InlineChips({ text }: Props) {
  const parts: React.ReactNode[] = [];
  const re = new RegExp(PLACEHOLDER_RE.source, 'g');
  let last = 0;
  let match: RegExpExecArray | null;

  while ((match = re.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    parts.push(
      <span
        key={`chip-${match.index}`}
        className="inline font-mono text-[0.78em] font-medium px-[5px] py-[1px]
                   rounded-[4px] bg-chip text-chipTxt border border-chipBdr
                   whitespace-nowrap"
      >
        {match[0]}
      </span>
    );
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return <>{parts}</>;
}
