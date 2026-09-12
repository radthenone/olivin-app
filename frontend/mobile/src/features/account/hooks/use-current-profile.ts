import { useQuery } from "@tanstack/react-query";
import { accountQueryKeys } from "../constants/account-query-keys";
import { profileService } from "../services/profile.service";

/**
 * Pobiera profil aktualnie zalogowanego użytkownika.
 *
 * Dlaczego istnieje:
 * profil jest danymi z backendu, więc powinien być cache'owany jako
 * server state w TanStack Query, a nie trzymany w Zustand.
 */
export function useCurrentProfile(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: accountQueryKeys.currentProfile(),
    queryFn: profileService.getCurrentProfile,
    enabled: options?.enabled ?? true,
  });
}
