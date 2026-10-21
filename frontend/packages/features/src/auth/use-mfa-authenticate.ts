import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postAllauthClientV1Auth2faAuthenticate } from "@olivin/api/generated/auth/authentication-2fa/authentication-2fa";

import { getAuthClient } from "./auth-config";
import { requireAuthStatus } from "./auth-response";
import { getAuthSessionQueryKey } from "./session-query-key";

export type MfaInput = {
  code: string;
};

/**
 * Potwierdza wymagany kod MFA po logowaniu.
 */
export function useMfaAuthenticate() {
  const queryClient = useQueryClient();
  const client = getAuthClient();

  return useMutation({
    mutationFn: async (data: MfaInput) => {
      const response = await postAllauthClientV1Auth2faAuthenticate(
        client,
        data,
      );

      requireAuthStatus(response, [200, 401], "Nie udało się potwierdzić MFA.");

      return response;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: getAuthSessionQueryKey(),
      });
    },
  });
}
