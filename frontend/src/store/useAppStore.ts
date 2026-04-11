import { create } from 'zustand';
import type { ChatMessage, DocState, View } from '../types';

interface AppStore {
  doc: DocState | null;
  chatHistory: ChatMessage[];
  uploadSummary: string;
  view: View;
  isLoading: boolean;
  loadingMessage: string;

  setDoc: (doc: DocState, uploadSummary?: string) => void;
  clearDoc: () => void;
  addMessage: (msg: ChatMessage) => void;
  setView: (view: View) => void;
  setLoading: (loading: boolean, message?: string) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  doc: null,
  chatHistory: [],
  uploadSummary: '',
  view: 'chat',
  isLoading: false,
  loadingMessage: '',

  setDoc: (doc, uploadSummary = '') => set({ doc, chatHistory: [], uploadSummary, view: 'redacted' }),
  clearDoc: () =>
    set({
      doc: null,
      chatHistory: [],
      uploadSummary: '',
      view: 'chat',
      isLoading: false,
      loadingMessage: '',
    }),
  addMessage: (msg) => set((s) => ({ chatHistory: [...s.chatHistory, msg] })),
  setView: (view) => set({ view }),
  setLoading: (isLoading, loadingMessage = '') => set({ isLoading, loadingMessage }),
}));
