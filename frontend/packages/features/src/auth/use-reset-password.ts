import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postAllauthClientV1AuthPasswordReset } from "@olivin/api/generated/auth/authentication-password-reset/authentication-password-reset";

import { getAuthClient } from "./auth-config";
import { requireAuthStatus } from "./auth-response";
import { getAuthSessionQueryKey } from "./session-query-key";

export type ResetPasswordInput = {
  key: string;
  password: string;
};

/**
 * Ustawia nowe hasło kodem resetu z maila (allauth przyjmuje go jako `key`).
 */
export function useResetPassword() {
  const queryClient = useQueryClient();
  const client = getAuthClient();

  return useMutation({
    mutationFn: async (data: ResetPasswordInput) => {
      const response = await postAllauthClientV1AuthPasswordReset(client, data);

      requireAuthStatus(response, [200, 401], "Nie udało się ustawić hasła.");

      return response;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: getAuthSessionQueryKey(),
      });
    },
  });
}
