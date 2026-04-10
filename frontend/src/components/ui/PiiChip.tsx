interface Props {
  label: string;
  index: number;
}

export default function PiiChip({ label, index }: Props) {
  return (
    <span className="inline font-mono text-[0.78em] font-medium px-[6px] py-[1px] rounded-[4px] bg-black text-neutral-300 border border-neutral-800">
      [{label}_{index}]
    </span>
  );
}
