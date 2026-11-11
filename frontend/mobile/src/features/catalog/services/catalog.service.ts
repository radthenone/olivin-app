import {
  createCatalogClient,
  type CatalogClient,
} from "@olivin/features/catalog";
import { ENV } from "@core/config/env";
import { getActiveLocale } from "@core/i18n";

/**
 * Klient publicznego API katalogu dla aplikacji mobilnej (ADR 0034).
 *
 * Zapytania realizowane są przez publiczny transport (bez poświadczeń sesji
 * ani nagłówka `X-Session-Token`), kierowane na adres bazowy API z konfiguracji
 * środowiska i wysyłają aktualny język interfejsu w `Accept-Language`.
 */
export const mobileCatalogClient: CatalogClient = createCatalogClient({
  baseUrl: () => {
    // Pozwala na nadpisanie adresu katalogu w e2e / Maestro lub testach
    const explicit =
      typeof process !== "undefined"
        ? process.env.EXPO_PUBLIC_CATALOG_API_URL || process.env.CATALOG_API_URL
        : undefined;
    return explicit || ENV.API_BASE_URL;
  },
  fetch: async (input, init) => {
    const headers = new Headers(init?.headers);
    if (!headers.has("accept-language")) {
      headers.set("accept-language", getActiveLocale());
    }
    return fetch(input, {
      ...init,
      headers,
    });
  },
});
