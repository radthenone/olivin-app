import {
  customersProfileList,
  customersProfilePartialUpdate,
} from "@olivin/api/generated/apps/profiles/profiles";

import {
  DELIVERY_COUNTRY_COOKIE_NAME,
  isEuDeliveryCountry,
  type DeliveryCountry,
} from "./delivery-country";

/**
 * Zapisuje kraj dostawy w ciasteczku przeglądarki (ADR 0035).
 *
 * Ważność: 1 rok. Flaga `Secure` jest dodawana wyłącznie przy połączeniu HTTPS.
 *
 * Args:
 *     country: Kraj dostawy wybrany przez klienta (UE).
 */
export function saveDeliveryCountryCookie(country: DeliveryCountry): void {
  if (typeof document === "undefined") {
    return;
  }
  const isHttps =
    typeof location !== "undefined" && location.protocol === "https:";
  const secure = isHttps ? "; Secure" : "";
  document.cookie = `${DELIVERY_COUNTRY_COOKIE_NAME}=${country}; path=/; max-age=31536000; SameSite=Lax${secure}`;
}

/**
 * Odczytuje zapisany w ciasteczku kraj dostawy.
 *
 * Returns:
 *     Prawidłowy kod kraju UE lub `null`, jeśli ciasteczko nie istnieje lub ma błędną wartość.
 */
export function readDeliveryCountryCookie(): DeliveryCountry | null {
  if (typeof document === "undefined") {
    return null;
  }
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${DELIVERY_COUNTRY_COOKIE_NAME}=`));

  if (!match) {
    return null;
  }

  const value = match.split("=")[1];
  return isEuDeliveryCountry(value) ? value : null;
}

/**
 * Pobiera profil zalogowanego klienta (pierwszy wynik listy).
 *
 * Returns:
 *     Profil klienta albo `undefined`, gdy odpowiedź nie zawiera wyników.
 */
async function fetchOwnProfile() {
  const listRes = await customersProfileList();
  return listRes.data.results?.[0];
}

/**
 * Zapisuje kraj dostawy w profilu zalogowanego klienta (ADR 0035, #363).
 *
 * Pobiera profil użytkownika i aktualizuje pole `deliveryCountry`.
 *
 * Args:
 *     country: Kod kraju dostawy.
 *
 * Throws:
 *     Error w przypadku braku profilu lub niepowodzenia zapisu API.
 */
export async function saveProfileDeliveryCountry(
  country: DeliveryCountry,
): Promise<void> {
  const profile = await fetchOwnProfile();

  if (!profile?.id) {
    throw new Error("Nie znaleziono profilu klienta.");
  }

  await customersProfilePartialUpdate(profile.id, {
    deliveryCountry: country,
  });
}

export type SyncDeliveryCountryResult = {
  country: DeliveryCountry | null;
  source: "profile" | "cookie" | "none";
};

/**
 * Synchronizuje kraj dostawy po zalogowaniu klienta (ADR 0035, #363).
 *
 * Reguły:
 * - Jeśli profil klienta zawiera zapisany kraj dostawy, nadpisuje ciasteczko w przeglądarce.
 * - Jeśli profil jest pusty, przejmuje aktualną wartość z ciasteczka (jeśli istnieje).
 * - Błędy komunikacji z API profilu nie przerywają logowania.
 *
 * Returns:
 *     Obiekt z ustalonym krajem dostawy i źródłem ('profile', 'cookie' lub 'none').
 */
export async function syncDeliveryCountryOnLogin(): Promise<SyncDeliveryCountryResult> {
  const currentCookie = readDeliveryCountryCookie();

  try {
    const profile = await fetchOwnProfile();

    const profileCountry = profile?.deliveryCountry;

    if (profileCountry && isEuDeliveryCountry(profileCountry)) {
      saveDeliveryCountryCookie(profileCountry);
      return { country: profileCountry, source: "profile" };
    }

    if (currentCookie && profile?.id) {
      try {
        await customersProfilePartialUpdate(profile.id, {
          deliveryCountry: currentCookie,
        });
      } catch {
        // Błąd zapisu profilu nie cofa wyboru w ciasteczku
      }
      return { country: currentCookie, source: "cookie" };
    }
  } catch {
    // Niepowodzenie pobrania profilu nie powinno blokować zalogowania
  }

  return { country: currentCookie ?? null, source: "none" };
}
