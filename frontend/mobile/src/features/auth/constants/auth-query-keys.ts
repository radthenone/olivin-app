import { allauthClient } from "@core/config/platform";

/**
 * Query keys dla auth.
 *
 * Dlaczego istnieje:
 * login, logout i session muszą invalidować te same przewidywalne klucze.
 */
export const authQueryKeys = {
  all: ["auth"] as const,
  session: () => [...authQueryKeys.all, "session", allauthClient] as const,
};
