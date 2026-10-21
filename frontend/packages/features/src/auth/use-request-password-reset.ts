import { useMutation } from "@tanstack/react-query";
import { postAllauthClientV1AuthPasswordRequest } from "@olivin/api/generated/auth/authentication-password-reset/authentication-password-reset";

import { getAuthClient } from "./auth-config";
import { requireAuthStatus } from "./auth-response";

export type RequestPasswordResetInput = {
  email: string;
};

/**
 * Wysyła prośbę o reset hasła.
 */
export function useRequestPasswordReset() {
  const client = getAuthClient();

  return useMutation({
    mutationFn: async (data: RequestPasswordResetInput) => {
      const response = await postAllauthClientV1AuthPasswordRequest(
        client,
        data,
      );

      requireAuthStatus(
        response,
        [200, 401],
        "Nie udało się wysłać resetu hasła.",
      );

      return response;
    },
  });
}
