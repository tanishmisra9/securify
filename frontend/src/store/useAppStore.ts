import { create } from 'zustand';
import type { ChatMessage, DocState, View } from '../types';

interface AppStore {
  doc: DocState | null;
  chatHistory: ChatMessage[];
  view: View;
  isLoading: boolean;
  loadingMessage: string;

  setDoc: (doc: DocState) => void;
  clearDoc: () => void;
  addMessage: (msg: ChatMessage) => void;
  setView: (view: View) => void;
  setLoading: (loading: boolean, message?: string) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  doc: null,
  chatHistory: [],
  view: 'chat',
  isLoading: false,
  loadingMessage: '',

  setDoc: (doc) => set({ doc, chatHistory: [], view: 'chat' }),
  clearDoc: () => set({ doc: null, chatHistory: [], view: 'chat' }),
  addMessage: (msg) => set((s) => ({ chatHistory: [...s.chatHistory, msg] })),
  setView: (view) => set({ view }),
  setLoading: (isLoading, loadingMessage = '') => set({ isLoading, loadingMessage }),
}));
