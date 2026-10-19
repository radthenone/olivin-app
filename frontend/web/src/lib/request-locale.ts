import { defaultLocale, type Locale } from "@olivin/i18n";

/**
 * Język, który interfejs pokazuje w danej chwili.
 *
 * Ten sam język trafia do nagłówka `Accept-Language` klienta API, żeby treści
 * z backendu (np. opisy produktów) zgadzały się z resztą ekranu (ADR 0035).
 *
 * Stan żyje tylko w przeglądarce. Na serwerze moduł jest współdzielony między
 * równoległymi żądaniami, więc globalny język przeciekałby między klientami —
 * tam `getApiLocale()` zwraca `undefined`, a wywołujący z serwera podaje
 * `accept-language` jawnie w nagłówkach żądania.
 */
let browserLocale: Locale = defaultLocale;

const isBrowser = (): boolean => typeof window !== "undefined";

export function setApiLocale(locale: Locale): void {
  if (isBrowser()) {
    browserLocale = locale;
  }
}

export function getApiLocale(): Locale | undefined {
  return isBrowser() ? browserLocale : undefined;
}
