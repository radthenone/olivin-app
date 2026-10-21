import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postAllauthClientV1AuthLogin } from "@olivin/api/generated/auth/authentication-account/authentication-account";

import { getAuthClient } from "./auth-config";
import { mapAllauthBodyToAuthState } from "./auth-mapper";
import { requireAuthStatus } from "./auth-response";
import { getAuthSessionQueryKey } from "./session-query-key";

export type LoginCredentials = {
  email: string;
  password: string;
};

/**
 * Logowanie e-mailem i hasłem.
 *
 * Po odpowiedzi unieważnia wyłącznie wygenerowany klucz sesji, więc routing
 * i każdy odbiorca sesji widzą nowy stan bez ręcznej synchronizacji.
 */
export function useLogin() {
  const queryClient = useQueryClient();
  const client = getAuthClient();

  const mutation = useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      const response = await postAllauthClientV1AuthLogin(client, credentials);

      requireAuthStatus(response, [200, 401], "Nie udało się zalogować.");

      return {
        response,
        state: mapAllauthBodyToAuthState(response.data),
      };
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: getAuthSessionQueryKey(),
      });
    },
  });

  return {
    ...mutation,
    login: async (credentials: LoginCredentials) => {
      const { response } = await mutation.mutateAsync(credentials);
      return response;
    },
  };
}
