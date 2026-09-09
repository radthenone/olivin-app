/**
 * Query keys dla danych konta użytkownika.
 *
 * Dlaczego istnieje:
 * profil i adresy są server state, więc wszystkie hooki konta powinny
 * invalidować przewidywalne, wspólne klucze TanStack Query.
 */
export const accountQueryKeys = {
  all: ["account"] as const,
  profile: () => [...accountQueryKeys.all, "profile"] as const,
  currentProfile: () => [...accountQueryKeys.profile(), "current"] as const,
  security: () => [...accountQueryKeys.all, "security"] as const,
  totpAuthenticator: () =>
    [...accountQueryKeys.security(), "totp-authenticator"] as const,
  addresses: () => [...accountQueryKeys.all, "addresses"] as const,
  address: (id: string) => [...accountQueryKeys.addresses(), id] as const,
};
