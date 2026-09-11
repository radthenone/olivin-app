import { useMutation } from "@tanstack/react-query";
import { authService } from "@core/auth/auth.service";

/**
 * Wysyła prośbę o reset hasła.
 */
export function useRequestPasswordReset() {
  return useMutation({
    mutationFn: authService.requestPasswordReset,
  });
}
