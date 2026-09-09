import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authService } from "@core/auth/auth.service";
import { authQueryKeys } from "../constants/auth-query-keys";

/**
 * Mutation logowania.
 *
 * Dlaczego istnieje:
 * po loginie odświeżamy session query, żeby routing sam przeszedł do app.
 */
export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authService.login,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: authQueryKeys.all });
    },
  });
}
