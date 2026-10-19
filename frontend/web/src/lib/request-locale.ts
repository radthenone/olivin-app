import { defaultLocale, type Locale } from "@olivin/i18n";

/**
 * Język, który interfejs pokazuje w danej chwili.
 *
 * Ten sam język trafia do nagłówka `Accept-Language` klienta API, żeby treści
 * z backendu (np. opisy produktów) zgadzały się z resztą ekranu (ADR 0035).
 * Provider ustawia go z `next-intl` przy każdym renderze.
 */
let apiLocale: Locale = defaultLocale;

export function setApiLocale(locale: Locale): void {
  apiLocale = locale;
}

export function getApiLocale(): Locale {
  return apiLocale;
}
