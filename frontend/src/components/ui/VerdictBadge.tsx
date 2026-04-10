interface Props {
  verdict: string;
}

export default function VerdictBadge({ verdict }: Props) {
  const isPass = verdict === 'PASS';
  return (
    <span
      className={[
        'inline-block px-2.5 py-0.5 rounded-full font-mono text-[0.65rem] font-medium',
        isPass
          ? 'bg-success/10 border border-success/25 text-success'
          : 'bg-danger/10 border border-danger/25 text-danger',
      ].join(' ')}
    >
      {verdict}
    </span>
  );
}
