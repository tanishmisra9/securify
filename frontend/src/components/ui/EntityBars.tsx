import { motion } from 'framer-motion';

interface Props {
  counts: Record<string, number>;
  confidences: Record<string, number>;
}

export default function EntityBars({ counts, confidences }: Props) {
  const labels = Object.keys(counts).sort();
  const max = Math.max(...Object.values(counts), 1);

  return (
    <div className="flex flex-col gap-[5px]">
      {labels.map((label, i) => {
        const count = counts[label];
        const conf = confidences[label] ?? 0.9;
        const pct = (count / max) * 100;

        return (
          <motion.div
            key={label}
            className="flex items-center gap-2"
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <span className="w-[86px] font-mono text-[0.67rem] text-t2 truncate flex-shrink-0">
              {label}
            </span>
            <span className="w-[16px] text-right text-[0.7rem] font-semibold text-t1 flex-shrink-0">
              {count}
            </span>
            <div className="flex-1 h-[3px] bg-border2 rounded-full overflow-hidden min-w-[20px]">
              <motion.div
                className="h-full bg-accent rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.5, delay: i * 0.05 + 0.1, ease: 'easeOut' }}
              />
            </div>
            <span className="w-[30px] text-right text-[0.63rem] text-t3 flex-shrink-0">
              {Math.round(conf * 100)}%
            </span>
          </motion.div>
        );
      })}
    </div>
  );
}
