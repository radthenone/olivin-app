import { useQueryClient } from "@tanstack/react-query";
import {
  getGetAllauthClientV1AuthSessionQueryKey,
  useDeleteAllauthClientV1AuthSession,
} from "@olivin/api/generated/auth/authentication-current-session/authentication-current-session";

import { AUTH_CLIENT } from "./auth-client";

/**
 * Wylogowanie z bieżącej sesji przeglądarkowej.
 *
 * Po odpowiedzi unieważnia wygenerowany klucz sesji, więc nagłówek od razu
 * przestaje pokazywać konto.
 */
export function useLogout() {
  const queryClient = useQueryClient();

  const mutation = useDeleteAllauthClientV1AuthSession({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getGetAllauthClientV1AuthSessionQueryKey(AUTH_CLIENT),
        });
      },
    },
  });

  return {
    logout: () => mutation.mutateAsync({ client: AUTH_CLIENT }),
    isPending: mutation.isPending,
  };
}
