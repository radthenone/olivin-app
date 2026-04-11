/**
 * auth.store.ts
 *
 * Globalny stan auth oparty na Zustand.
 * Przechowuje surową odpowiedź z endpointu session (meta + ewentualne flows).
 */
import { create } from "zustand";
import type { AuthSessionState, AuthState } from "./auth.types";

interface AuthStore extends AuthState {
  setSession: (session: AuthSessionState) => void;
  resetSession: () => void;
}

const initialState: AuthState = {
  session: undefined,
};

export const useAuthStore = create<AuthStore>((set) => ({
  ...initialState,

  setSession: (session) => set({ session }),
  resetSession: () => set({ session: null }),
}));
