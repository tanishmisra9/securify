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
          className="flex-shrink-0 border-b border-border bg-surface2/50 backdrop-blur-sm
                     px-8 py-2 flex items-center gap-5 min-w-0"
        >
          <div className="flex items-center gap-2 min-w-0">
            <FileText size={12} strokeWidth={1.75} className="text-t3 flex-shrink-0" />
            <span className="font-mono text-[0.72rem] text-t2 truncate">{doc.filename}</span>
          </div>

          <div className="flex items-center gap-1.5 flex-shrink-0">
            <ShieldCheck size={12} strokeWidth={1.75} className="text-success" />
            <span className="text-[0.72rem] text-t3">
              <span className="text-success font-semibold font-mono">
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
                <div key={label} className="flex items-center gap-1">
                  <span className="font-mono text-[0.62rem] text-t3 uppercase">{label}</span>
                  <span className="font-mono text-[0.63rem] text-accent font-medium">
                    {count}
                  </span>
                </div>
              ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
