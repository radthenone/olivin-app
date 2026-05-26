import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authService } from "@core/auth/auth.service";
import { authQueryKeys } from "../constants/auth-query-keys";

/**
 * Potwierdza email kodem/kluczem z allauth.
 *
 * Dlaczego istnieje:
 * po poprawnej weryfikacji backend może ustawić zalogowaną sesję,
 * więc routing powinien dostać świeży stan z `auth/session`.
 */
export function useVerifyEmail() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authService.verifyEmail,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: authQueryKeys.all });
    },
  });
}
