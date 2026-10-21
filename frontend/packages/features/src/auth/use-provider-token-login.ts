import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postAllauthClientV1AuthProviderToken } from "@olivin/api/generated/auth/authentication-providers/authentication-providers";

import { getAuthClient } from "./auth-config";
import { mapAllauthBodyToAuthState } from "./auth-mapper";
import { requireAuthStatus } from "./auth-response";
import { getAuthSessionQueryKey } from "./session-query-key";

export type ProviderTokenLoginInput =
  | {
      provider: "google";
      clientId: string;
      idToken: string;
    }
  | {
      provider: "facebook";
      clientId: string;
      accessToken: string;
    };

/**
 * Loguje przez token dostawcy (Google ID token, Facebook access token).
 *
 * Stan `provider_signup_required` od razu ląduje w cache sesji, żeby routing
 * przeniósł na ekran zgód, zanim zdąży wykonać się refetch.
 */
export function useProviderTokenLogin() {
  const queryClient = useQueryClient();
  const client = getAuthClient();

  return useMutation({
    mutationFn: async (data: ProviderTokenLoginInput) => {
      const token =
        data.provider === "google"
          ? { client_id: data.clientId, id_token: data.idToken }
          : { client_id: data.clientId, access_token: data.accessToken };

      const response = await postAllauthClientV1AuthProviderToken(client, {
        provider: data.provider,
        process: "login",
        token,
      });

      requireAuthStatus(
        response,
        [200, 401],
        "Nie udało się zalogować social.",
      );

      return {
        response,
        state: mapAllauthBodyToAuthState(response.data),
      };
    },
    onSuccess: async ({ response, state }) => {
      const queryKey = getAuthSessionQueryKey();

      if (state.status === "provider_signup_required") {
        queryClient.setQueryData(queryKey, response);
      }

      await queryClient.invalidateQueries({ queryKey });
    },
  });
}
