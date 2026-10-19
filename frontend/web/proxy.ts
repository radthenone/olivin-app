import createMiddleware from "next-intl/middleware";

import { localeMatcher } from "@/i18n/matcher";
import { routing } from "@/i18n/routing";

/**
 * Przekierowanie `/` na język klienta i obsługa prefiksu `/pl` albo `/en`.
 *
 * Kolejność detekcji: cookie języka, `Accept-Language`, domyślnie `/pl`.
 * Matcher zostawia poza proxy adresy techniczne — patrz `src/i18n/matcher.ts`.
 */
export default createMiddleware(routing);

export const config = {
  matcher: localeMatcher,
};
