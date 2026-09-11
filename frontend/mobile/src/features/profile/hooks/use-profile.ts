import { useCurrentProfile } from "@features/account/hooks/use-current-profile";

/**
 * Pobiera profil aktualnie zalogowanego użytkownika.
 *
 * Dlaczego istnieje:
 * zachowuje kompatybilność ze starszym importem `features/profile`.
 * Nowy kod powinien używać `features/account`.
 */
export function useProfile() {
  return useCurrentProfile();
}
