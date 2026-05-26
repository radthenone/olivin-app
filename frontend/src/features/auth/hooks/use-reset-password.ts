import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authService } from "@core/auth/auth.service";
import { authQueryKeys } from "../constants/auth-query-keys";

/**
 * Ustawia nowe hasło na podstawie klucza resetu.
 */
export function useResetPassword() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authService.resetPassword,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: authQueryKeys.all });
    },
  });
}
