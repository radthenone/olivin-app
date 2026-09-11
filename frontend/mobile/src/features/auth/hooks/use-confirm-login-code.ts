import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authService } from "@core/auth/auth.service";
import { authQueryKeys } from "../constants/auth-query-keys";

/**
 * Potwierdza jednorazowy kod logowania.
 */
export function useConfirmLoginCode() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authService.confirmLoginCode,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: authQueryKeys.all });
    },
  });
}
