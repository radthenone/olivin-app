import en from "./messages/en.json";
import pl from "./messages/pl.json";

/**
 * Wspólny katalog komunikatów ICU.
 *
 * `pl.json` jest źródłem: jego klucze i przestrzenie nazw opisują interfejs.
 * `en.json` jest tłumaczeniem i musi mieć dokładnie ten sam zestaw kluczy.
 * Web konsumuje katalog przez `next-intl`, mobile przez `use-intl`.
 *
 * Patrz docs/adr/0035-next-intl-z-prefiksem-jezyka-waluta-z-kraju-dostawy.md
 */
export const locales = ["pl", "en"] as const;

export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "pl";

/** Nazwa cookie, którą next-intl zapisuje i odczytuje przy przekierowaniu `/`. */
export const localeCookieName = "NEXT_LOCALE";

/** Klucze komunikatów wynikają wprost z `pl.json`. */
export type Messages = typeof pl;

export const messages: Record<Locale, Messages> = {
  pl,
  en,
};

export function isLocale(value: unknown): value is Locale {
  return (
    typeof value === "string" && (locales as readonly string[]).includes(value)
  );
}
