import { useQuery } from "@tanstack/react-query";
import { authService } from "@core/auth/auth.service";
import { authQueryKeys } from "../constants/auth-query-keys";

/**
 * Pobiera aktualną sesję z allauth.
 *
 * Dlaczego istnieje:
 * sesja jest server state, więc trzymamy ją w TanStack Query, nie w Zustand.
 */
export function useSession() {
  return useQuery({
    queryKey: authQueryKeys.session(),
    queryFn: authService.getSession,
    retry: false,
  });
}
