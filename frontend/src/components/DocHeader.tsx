import { AnimatePresence, motion } from 'framer-motion';
import { FileText, ShieldCheck } from 'lucide-react';

import { useAppStore } from '../store/useAppStore';

export default function DocHeader() {
  const { doc } = useAppStore();

  return (
    <AnimatePresence>
      {doc && (
        <motion.div
          key="doc-header"
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.18 }}
          className="flex-shrink-0 border-b border-border bg-[rgba(15,22,36,0.8)] backdrop-blur-glass px-8 py-2 flex items-center gap-5 min-w-0"
          style={{ boxShadow: 'inset 0 -1px 0 rgba(255,255,255,0.04)' }}
        >
          <div className="flex items-center gap-2 min-w-0">
            <FileText size={12} strokeWidth={1.75} className="text-t3 flex-shrink-0" />
            <span className="font-mono text-[0.72rem] text-t2 truncate">{doc.filename}</span>
          </div>

          <div className="flex items-center gap-1.5 flex-shrink-0">
            <ShieldCheck size={12} strokeWidth={1.75} className="text-accent" />
            <span className="text-[0.72rem] text-t3">
              <span className="text-accent font-semibold font-mono">
                {doc.total_entities}
              </span>{' '}
              entities redacted
            </span>
          </div>

          <div className="flex items-center gap-4 ml-auto flex-shrink-0">
            {Object.entries(doc.entity_counts)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 5)
              .map(([label, count]) => (
                <div
                  key={label}
                  className="flex items-center gap-1 bg-[rgba(59,130,246,0.08)] border border-[rgba(59,130,246,0.18)] rounded-full px-2 py-0.5"
                >
                  <span className="font-mono text-[0.6rem] text-t3 uppercase">{label}</span>
                  <span className="font-mono text-[0.6rem] text-accent font-medium">{count}</span>
                </div>
              ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
