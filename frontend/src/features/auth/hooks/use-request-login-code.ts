import { useMutation } from "@tanstack/react-query";
import { authService } from "@core/auth/auth.service";

/**
 * Wysyła jednorazowy kod logowania na email.
 */
export function useRequestLoginCode() {
  return useMutation({
    mutationFn: authService.requestLoginCode,
  });
}
