import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authService } from "@core/auth/auth.service";
import { authQueryKeys } from "../constants/auth-query-keys";

/**
 * Potwierdza wymagany kod MFA po logowaniu.
 */
export function useMfaAuthenticate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authService.authenticateMfa,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: authQueryKeys.all });
    },
  });
}
