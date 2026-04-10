import { motion } from 'framer-motion';
import { Shield } from 'lucide-react';

const STATS = [
  { val: 'NER', label: 'Transformer model' },
  { val: '10+', label: 'PII entity types' },
  { val: '0', label: 'PII to the LLM' },
];

export default function EmptyState() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-8">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        className="w-16 h-16 rounded-2xl bg-surface border border-border flex items-center justify-center mb-6 shadow-xl shadow-accent/5"
      >
        <Shield size={26} className="text-accent" strokeWidth={1.75} />
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="text-[1.4rem] font-semibold tracking-tight text-t1 mb-3"
      >
        Upload a document to begin
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="text-t3 text-[0.88rem] leading-relaxed max-w-[360px] mb-10"
      >
        Securify redacts all PII before your document reaches the LLM. Ask anything — names,
        SSNs, and account numbers never leave your machine unmasked.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="flex gap-10"
      >
        {STATS.map(({ val, label }, i) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + i * 0.07 }}
            className="text-center"
          >
            <p className="font-mono text-[1.3rem] text-accent font-medium">{val}</p>
            <p className="text-t3 text-[0.68rem] mt-1">{label}</p>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
