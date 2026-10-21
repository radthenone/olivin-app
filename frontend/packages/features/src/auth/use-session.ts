import { useGetAllauthClientV1AuthSession } from "@olivin/api/generated/auth/authentication-current-session/authentication-current-session";
import type { User } from "@olivin/api/generated/auth/schemas/user";

import { getAuthClient } from "./auth-config";
import { mapAllauthBodyToAuthState } from "./auth-mapper";

export type AuthUser = User;

/**
 * Bieżąca sesja allauth jako stan gotowy dla interfejsu.
 *
 * Query pochodzi z Orvala, a mapowanie zdejmuje z UI statusy 401/410 oraz
 * flows. Klucz zapytania jest wygenerowany, więc każda invalidacja trafia w
 * ten sam cache.
 */
export function useSession() {
  const query = useGetAllauthClientV1AuthSession(getAuthClient(), {
    query: { retry: false },
  });

  const state = mapAllauthBodyToAuthState(query.data?.data);

  return {
    query,
    state,
    user: state.status === "authenticated" ? state.user : null,
    isAuthenticated: state.status === "authenticated",
    isChecking: query.isPending,
  };
}
