import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authService } from "@core/auth/auth.service";
import { accountQueryKeys } from "@features/account/constants/account-query-keys";
import { authQueryKeys } from "../constants/auth-query-keys";

/**
 * Kończy aktualną sesję użytkownika.
 *
 * Dlaczego istnieje:
 * logout musi wyczyścić cache auth, żeby routing i UI nie korzystały
 * z poprzedniego stanu sesji.
 */
export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authService.logout,
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: authQueryKeys.all });
      queryClient.removeQueries({ queryKey: accountQueryKeys.all });
      await queryClient.invalidateQueries({ queryKey: authQueryKeys.all });
    },
  });
}
