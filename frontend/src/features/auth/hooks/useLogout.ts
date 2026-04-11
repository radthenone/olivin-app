/**
 * useLogout.ts
 *
 * Hook do wylogowania użytkownika.
 * Po wylogowaniu resetuje store i nawiguje do ekranu logowania.
 */
import { useState } from "react";
import { authService, useAuthStore } from "@core/auth";

export interface UseLogoutResult {
  logout: () => Promise<void>;
  isLoading: boolean;
}

export function useLogout(): UseLogoutResult {
  const { resetSession } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);

  const logout = async () => {
    setIsLoading(true);

    try {
      await authService.logout();
    } catch {
      // Ignoruj błędy sieciowe — wylogowanie lokalne jest zawsze wykonywane
    } finally {
      resetSession();
      setIsLoading(false);
    }
  };

  return { logout, isLoading };
}
