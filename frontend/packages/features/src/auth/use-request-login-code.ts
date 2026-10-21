import { useMutation } from "@tanstack/react-query";
import { postAllauthClientV1AuthCodeRequest } from "@olivin/api/generated/auth/authentication-login-by-code/authentication-login-by-code";

import { getAuthClient } from "./auth-config";
import { requireAuthStatus } from "./auth-response";

export type RequestLoginCodeInput = {
  email: string;
};

/**
 * Wysyła jednorazowy kod logowania na email.
 */
export function useRequestLoginCode() {
  const client = getAuthClient();

  return useMutation({
    mutationFn: async (data: RequestLoginCodeInput) => {
      const response = await postAllauthClientV1AuthCodeRequest(client, data);

      requireAuthStatus(
        response,
        [200, 401],
        "Nie udało się wysłać kodu logowania.",
      );

      return response;
    },
  });
}
