import { useMutation, useQueryClient } from "@tanstack/react-query";
import { getAuthSessionQueryKey } from "@olivin/features/auth";
import { securityService } from "../services/security.service";

/**
 * Rozpoczyna zmianę adresu email przez allauth.
 */
export function useRequestEmailChange() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: securityService.requestEmailChange,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: getAuthSessionQueryKey(),
      });
    },
  });
}
