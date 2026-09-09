import { useMutation, useQueryClient } from "@tanstack/react-query";
import { accountQueryKeys } from "../constants/account-query-keys";
import { securityService } from "../services/security.service";

/**
 * Aktywuje TOTP i odświeża stan ustawień bezpieczeństwa.
 */
export function useActivateTotp() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: securityService.activateTotp,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: accountQueryKeys.security(),
      });
    },
  });
}
