// Every TanStack Query key in the app comes from here. Add one entry per
// feature; nest keys so invalidating `queryKeys.<feature>.all` clears them all.

export const queryKeys = {
  health: {
    all: ["health"] as const,
  },
} as const;
