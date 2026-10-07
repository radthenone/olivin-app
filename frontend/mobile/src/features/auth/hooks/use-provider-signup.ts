import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authService } from "@core/auth/auth.service";
import { authQueryKeys } from "../constants/auth-query-keys";

/**
 * Dokańcza rejestrację po Google/Facebook (krok allauth `provider_signup`).
 *
 * Dlaczego istnieje:
 * nowe konto z logowania zewnętrznego powstaje dopiero po zgodach (#207);
 * po odpowiedzi odświeżamy auth cache, żeby routing przeszedł dalej.
 */
export function useProviderSignup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authService.providerSignup,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: authQueryKeys.all });
    },
  });
}
