import { AnimatePresence, motion } from 'framer-motion';

import AuditView from './components/AuditView';
import ChatView from './components/ChatView';
import EmptyState from './components/EmptyState';
import RedactedView from './components/RedactedView';
import Sidebar from './components/Sidebar';
import { useAppStore } from './store/useAppStore';

const pageVariants = {
  initial: { opacity: 0, x: 12 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.22, ease: 'easeOut' } },
  exit: { opacity: 0, x: -8, transition: { duration: 0.15 } },
};

export default function App() {
  const { doc, view } = useAppStore();

  if (!doc) {
    return (
      <div className="flex h-screen overflow-hidden bg-bg">
        <Sidebar />
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
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
          <div className="w-10 h-10 rounded-full border-2 border-border2 border-t-accent animate-spin" />
          <p className="text-t2 text-sm font-sans">{loadingMessage || 'Processing…'}</p>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
