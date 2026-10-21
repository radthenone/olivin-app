import { useQueryClient } from "@tanstack/react-query";
import {
  getGetAllauthClientV1AuthSessionQueryKey,
  useGetAllauthClientV1AuthSession,
} from "@olivin/api/generated/auth/authentication-current-session/authentication-current-session";
import { usePostAllauthClientV1AuthLogin } from "@olivin/api/generated/auth/authentication-account/authentication-account";

import { AUTH_CLIENT } from "./auth-client";

export type LoginCredentials = {
  email: string;
  password: string;
};

/**
 * Logowanie e-mailem i hasłem w trybie przeglądarkowym.
 *
 * Po udanej odpowiedzi unieważnia wyłącznie wygenerowany klucz sesji, więc
 * nagłówek i każdy inny odbiorca sesji widzą nowy stan bez ręcznej synchronizacji.
 */
export function useLogin() {
  const queryClient = useQueryClient();

  const mutation = usePostAllauthClientV1AuthLogin({
    mutation: {
      onSuccess: async (response) => {
        if (response.status !== 200) return;

        await queryClient.invalidateQueries({
          queryKey: getGetAllauthClientV1AuthSessionQueryKey(AUTH_CLIENT),
        });
      },
    },
  });

  return {
    login: (credentials: LoginCredentials) =>
      mutation.mutateAsync({ client: AUTH_CLIENT, data: credentials }),
    isPending: mutation.isPending,
  };
}
