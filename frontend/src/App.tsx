import { AnimatePresence, motion } from 'framer-motion';

import AuditView from './components/AuditView';
import ChatView from './components/ChatView';
import DocHeader from './components/DocHeader';
import EmptyState from './components/EmptyState';
import RedactedView from './components/RedactedView';
import Sidebar from './components/Sidebar';
import { useAppStore } from './store/useAppStore';

const pageVariants = {
  initial: { opacity: 0, filter: 'blur(8px)' },
  animate: {
    opacity: 1,
    filter: 'blur(0px)',
    transition: { duration: 0.32, ease: [0.22, 1, 0.36, 1] },
  },
  exit: { opacity: 0, filter: 'blur(4px)', transition: { duration: 0.18 } },
};

export default function App() {
  const { doc, view } = useAppStore();

  if (!doc) {
    return (
      <div className="flex h-screen overflow-hidden bg-bg">
        <Sidebar />
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <DocHeader />
          <div className="flex-1 min-h-0 overflow-hidden">
            <EmptyState />
          </div>
        </main>
        <LoadingOverlay />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-bg">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <DocHeader />
        <AnimatePresence mode="sync" initial={false}>
          {view === 'chat' ? (
            <motion.div key="chat" className="flex-1 flex flex-col min-h-0" {...pageVariants}>
              <ChatView />
            </motion.div>
          ) : view === 'redacted' ? (
            <motion.div key="redacted" className="flex-1 min-h-0 overflow-hidden" {...pageVariants}>
              <RedactedView />
            </motion.div>
          ) : (
            <motion.div key="audit" className="flex-1 min-h-0 overflow-hidden" {...pageVariants}>
              <AuditView />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <LoadingOverlay />
    </div>
  );
}

function LoadingOverlay() {
  const { isLoading, loadingMessage } = useAppStore();
  return (
    <AnimatePresence>
      {isLoading && (
        <motion.div
          key="overlay"
          className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-4
                     bg-bg/90 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, transition: { duration: 0.2 } }}
        >
          <div className="relative w-10 h-10">
            <div className="absolute inset-0 rounded-full border border-border2 animate-ping opacity-20" />
            <div className="absolute inset-0 rounded-full border-2 border-border2 border-t-accent animate-spin" />
          </div>
          <p className="text-t2 text-sm font-sans">{loadingMessage || 'Processing…'}</p>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
