import { useRef, useState } from 'react';

import { motion } from 'framer-motion';
import { Shield, Upload } from 'lucide-react';

import { useUpload } from '../hooks/useUpload';

const STATS = [
  { val: 'NER', label: 'Transformer model' },
  { val: '10+', label: 'PII entity types' },
  { val: '0', label: 'PII to the LLM' },
];

export default function EmptyState() {
  const { uploadFile, error, clearError } = useUpload();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFile = async (file: File | null) => {
    if (!file) return;
    try {
      await uploadFile(file);
    } catch {
      // surfaced via hook error state
    } finally {
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-8">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        className="w-20 h-20 rounded-full bg-[rgba(59,130,246,0.10)] flex items-center justify-center mb-6"
        style={{ boxShadow: '0 0 40px rgba(59,130,246,0.14)' }}
      >
        <Shield size={32} className="text-accent" strokeWidth={1.5} />
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="text-[1.5rem] font-semibold tracking-[-0.03em] text-t1 mb-3"
      >
        Upload your documents
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="text-t3 text-[0.88rem] leading-relaxed max-w-[360px] mb-10"
      >
        Drop a file below to begin. Securify redacts all PII before your document reaches the
        LLM, so names, SSNs, and account numbers never leave your machine unmasked.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.18 }}
        className="w-full max-w-[620px] mb-10"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(e) => void handleFile(e.target.files?.[0] ?? null)}
        />
        <button
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            void handleFile(e.dataTransfer.files?.[0] ?? null);
          }}
          className={[
            'w-full rounded-2xl border bg-[rgba(15,22,36,0.6)] backdrop-blur-glass px-8 py-12 transition-all duration-200 cursor-pointer',
            'shadow-[inset_0_1px_0_rgba(255,255,255,0.05),0_4px_20px_rgba(0,0,0,0.3)]',
            dragActive
              ? 'border-accent bg-[rgba(59,130,246,0.08)]'
              : 'border-[rgba(255,255,255,0.07)] hover:border-[rgba(59,130,246,0.4)]',
          ].join(' ')}
        >
          <div className="flex justify-center mb-4">
            <Upload size={22} className={dragActive ? 'text-accent' : 'text-t3'} strokeWidth={1.5} />
          </div>
          <div>
            <p className="text-t1 text-[1.1rem] font-semibold leading-tight">
              Drag and drop files here, or click to browse.
            </p>
          </div>
          <div className="mt-4 text-[0.68rem] text-t3 font-mono">Accepted: PDF · DOCX · TXT</div>
        </button>
        {error && (
          <div className="mt-3 text-[0.76rem] text-danger flex items-start justify-between gap-2">
            <span>{error}</span>
            <button className="text-t3 hover:text-t1" onClick={clearError}>
              ×
            </button>
          </div>
        )}
      </motion.div>

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
            transition={{ delay: 0.2 + i * 0.07, duration: 0.26, ease: [0.22, 1, 0.36, 1] }}
            className="text-center"
          >
            <p className="font-mono text-[1.4rem] text-accent font-medium tracking-[-0.02em]">{val}</p>
            <p className="text-t3 text-[0.68rem] mt-1">{label}</p>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
