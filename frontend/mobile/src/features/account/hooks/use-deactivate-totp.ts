import { useMutation, useQueryClient } from "@tanstack/react-query";
import { accountQueryKeys } from "../constants/account-query-keys";
import { securityService } from "../services/security.service";

/**
 * Wyłącza TOTP i odświeża stan ustawień bezpieczeństwa.
 */
export function useDeactivateTotp() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: securityService.deactivateTotp,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: accountQueryKeys.security(),
      });
    },
  });
}
