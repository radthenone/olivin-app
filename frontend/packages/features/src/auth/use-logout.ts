import { useMutation, useQueryClient } from "@tanstack/react-query";
import { deleteAllauthClientV1AuthSession } from "@olivin/api/generated/auth/authentication-current-session/authentication-current-session";

import { getAuthClient } from "./auth-config";
import { getAuthSessionQueryKey } from "./session-query-key";

export type LogoutOptions = {
  /**
   * Dodatkowe sprzątanie po stronie aplikacji — mobile czyści tu cache konta,
   * którego hooki zostają w aplikacji do plasterka konta (ADR 0033).
   */
  onLogout?: () => void | Promise<void>;
};

/**
 * Wylogowanie z bieżącej sesji.
 *
 * Usuwa wpis sesji, żeby routing i UI nie korzystały z poprzedniego stanu,
 * a potem unieważnia wygenerowany klucz zapytania.
 */
export function useLogout(options?: LogoutOptions) {
  const queryClient = useQueryClient();
  const client = getAuthClient();

  const mutation = useMutation({
    mutationFn: async () => {
      await deleteAllauthClientV1AuthSession(client);
    },
    onSuccess: async () => {
      const queryKey = getAuthSessionQueryKey();

      queryClient.removeQueries({ queryKey });
      await options?.onLogout?.();
      await queryClient.invalidateQueries({ queryKey });
    },
  });

  return {
    ...mutation,
    logout: () => mutation.mutateAsync(),
  };
}
