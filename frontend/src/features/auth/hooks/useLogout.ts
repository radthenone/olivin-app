/**
 * useLogout.ts
 *
 * Hook do wylogowania użytkownika.
 * Po wylogowaniu czyści session query; nawigacją zajmuje się guard.
 */
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { authService } from "@core/auth";
import { sessionQueryKey } from "./useSession";

export interface UseLogoutResult {
  logout: () => Promise<void>;
  isLoading: boolean;
}

export function useLogout(): UseLogoutResult {
  const queryClient = useQueryClient();
  const [isLoading, setIsLoading] = useState(false);

  const logout = async () => {
    setIsLoading(true);

    try {
      await authService.logout();
    } catch {
      // Ignoruj błędy sieciowe — wylogowanie lokalne jest zawsze wykonywane
    } finally {
      queryClient.setQueryData(sessionQueryKey, null);
      await queryClient.invalidateQueries({ queryKey: sessionQueryKey });
      setIsLoading(false);
    }
  };

  return { logout, isLoading };
}
