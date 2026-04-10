interface Props {
  label: string;
  index: number;
}

export default function PiiChip({ label, index }: Props) {
  return (
    <span className="inline font-mono text-[0.78em] font-medium px-[5px] py-[1px] rounded-[4px] bg-chip text-chipTxt border border-chipBdr">
      [{label}_{index}]
    </span>
  );
}
