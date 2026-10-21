import { useGetAllauthClientV1AuthSession } from "@olivin/api/generated/auth/authentication-current-session/authentication-current-session";
import type { User } from "@olivin/api/generated/auth/schemas/user";

import { AUTH_CLIENT } from "./auth-client";

export type AuthUser = User;

/**
 * Bieżąca sesja allauth jako stan gotowy dla interfejsu.
 *
 * Klucz zapytania pochodzi z Orvala — unieważnianie po loginie i logoutcie
 * trafia w ten sam cache, bez ręcznie składanych kluczy.
 */
export function useSession() {
  const query = useGetAllauthClientV1AuthSession(AUTH_CLIENT, {
    query: { retry: false },
  });

  const body = query.data?.status === 200 ? query.data.data : null;
  const user = (body?.data.user as AuthUser | undefined) ?? null;

  return {
    query,
    user,
    isAuthenticated: user !== null,
    isChecking: query.isPending,
  };
}
