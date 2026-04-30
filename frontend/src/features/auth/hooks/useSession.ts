import { useQuery } from "@tanstack/react-query";
import { CONFIG } from "@core/env";
import { authService } from "@core/auth";

export const sessionQueryKey = ["auth", "session", CONFIG.CLIENT] as const;

export function useSession() {
  return useQuery({
    queryKey: sessionQueryKey,
    queryFn: () => authService.getSession(),
    staleTime: 0,
    retry: false,
  });
}
