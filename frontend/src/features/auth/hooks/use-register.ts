import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authService } from "@core/auth/auth.service";
import { authQueryKeys } from "../constants/auth-query-keys";

/**
 * Rejestruje użytkownika przez allauth.
 *
 * Dlaczego istnieje:
 * signup może od razu zwrócić stan wymagający weryfikacji email albo
 * zalogowaną sesję, więc po odpowiedzi odświeżamy auth cache.
 */
export function useRegister() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authService.signup,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: authQueryKeys.all });
    },
  });
}
