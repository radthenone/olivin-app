import { defaultLocale, isLocale, type Locale } from "@olivin/i18n";

let currentLocale: Locale = defaultLocale;

const listeners = new Set<(locale: Locale) => void>();

/**
 * Zwraca aktualny język interfejsu aplikacji mobilnej.
 *
 * Wykorzystywany m.in. przez nagłówek Accept-Language klienta HTTP (ADR 0035).
 */
export function getActiveLocale(): Locale {
  return currentLocale;
}

/**
 * Ustawia aktywny język interfejsu aplikacji mobilnej.
 */
export function setActiveLocale(locale: Locale): void {
  if (!isLocale(locale)) {
    return;
  }
  if (currentLocale !== locale) {
    currentLocale = locale;
    listeners.forEach((listener) => listener(locale));
  }
}

/**
 * Subskrybuje zmiany aktywnego języka.
 */
export function subscribeLocale(listener: (locale: Locale) => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
