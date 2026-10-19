import { hasLocale } from "next-intl";
import { getRequestConfig } from "next-intl/server";
import { notFound } from "next/navigation";
import * as rootParams from "next/root-params";

import { messages } from "@olivin/i18n";

import { routing } from "./routing";

/**
 * Katalog komunikatów dla bieżącego żądania.
 *
 * `pl.json` jest źródłem, dlatego typy `next-intl` są oparte właśnie na nim.
 * Jawny `locale` (np. z `getTranslations({locale})`) ma pierwszeństwo przed
 * segmentem `[locale]`.
 */
export default getRequestConfig(async ({ locale }) => {
  const requested = locale ?? (await rootParams.locale());

  if (!hasLocale(routing.locales, requested)) {
    notFound();
  }

  return {
    locale: requested,
    messages: messages[requested],
  };
});
