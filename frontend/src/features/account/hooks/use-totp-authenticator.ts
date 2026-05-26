import { useQuery } from "@tanstack/react-query";
import { accountQueryKeys } from "../constants/account-query-keys";
import { securityService } from "../services/security.service";

/**
 * Pobiera status TOTP aktualnie zalogowanego użytkownika.
 */
export function useTotpAuthenticator() {
  return useQuery({
    queryKey: accountQueryKeys.totpAuthenticator(),
    queryFn: securityService.getTotpAuthenticator,
    gcTime: 10 * 60 * 1000,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
    retry: false,
    staleTime: 10 * 60 * 1000,
  });
}
