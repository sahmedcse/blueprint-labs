import { create } from "zustand";

// Client UI state shared across components. Never put server data here;
// that belongs to TanStack Query.
type UiState = {
  detailsOpen: boolean;
  toggleDetails: () => void;
};

export const useUiStore = create<UiState>()((set) => ({
  detailsOpen: false,
  toggleDetails: () => set((state) => ({ detailsOpen: !state.detailsOpen })),
}));
