import { hasLocale } from "next-intl";
import { getRequestConfig } from "next-intl/server";

import { messages } from "@olivin/i18n";

import { routing } from "./routing";

/**
 * Katalog komunikatów dla bieżącego żądania.
 *
 * `pl.json` jest źródłem, dlatego typy `next-intl` są oparte właśnie na nim.
 * Język przychodzi z segmentu `[locale]` (przez `setRequestLocale` w layoucie
 * albo z proxy) lub jawnie z `getTranslations({locale})`. Nieznany język
 * spada na domyślny — 404 dla złego prefiksu oddaje layout.
 */
export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested)
    ? requested
    : routing.defaultLocale;

  return {
    locale,
    messages: messages[locale],
  };
});
