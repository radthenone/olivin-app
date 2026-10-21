import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postAllauthClientV1AuthCodeConfirm } from "@olivin/api/generated/auth/authentication-login-by-code/authentication-login-by-code";

import { getAuthClient } from "./auth-config";
import { mapAllauthBodyToAuthState } from "./auth-mapper";
import { requireAuthStatus } from "./auth-response";
import { getAuthSessionQueryKey } from "./session-query-key";

export type ConfirmLoginCodeInput = {
  code: string;
};

/**
 * Potwierdza jednorazowy kod logowania.
 */
export function useConfirmLoginCode() {
  const queryClient = useQueryClient();
  const client = getAuthClient();

  return useMutation({
    mutationFn: async (data: ConfirmLoginCodeInput) => {
      const response = await postAllauthClientV1AuthCodeConfirm(client, data);

      requireAuthStatus(
        response,
        [200, 401],
        "Nie udało się potwierdzić kodu logowania.",
      );

      return mapAllauthBodyToAuthState(response.data);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: getAuthSessionQueryKey(),
      });
    },
  });
}
