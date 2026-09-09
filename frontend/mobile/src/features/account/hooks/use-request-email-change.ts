import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authQueryKeys } from "@features/auth/constants/auth-query-keys";
import { securityService } from "../services/security.service";

/**
 * Rozpoczyna zmianę adresu email przez allauth.
 */
export function useRequestEmailChange() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: securityService.requestEmailChange,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: authQueryKeys.all });
    },
  });
}
