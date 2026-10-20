import { defaultLocale, localeCookieName, locales } from "@olivin/i18n";
import { defineRouting } from "next-intl/routing";

/**
 * Routing języka (ADR 0035).
 *
 * Każda strona klienta ma prefiks `/pl` albo `/en`, także domyślny polski.
 * Ścieżek nie tłumaczymy — slug jest jeden, angielski.
 */
export const routing = defineRouting({
  locales,
  defaultLocale,
  localePrefix: "always",
  localeCookie: { name: localeCookieName },
});
