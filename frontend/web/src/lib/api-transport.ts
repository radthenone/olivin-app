import { configureApi } from "@olivin/api";

import { webRequest } from "./http";

/**
 * Implementacja transportu dla aplikacji webowej.
 *
 * Pakiet @olivin/api zna endpointy, ale nie wie, czym wykonać żądanie. Tutaj
 * podłączamy wariant przeglądarkowy: ciasteczka zamiast nagłówka z tokenem
 * sesji. Aplikacja mobilna dostarcza własny.
 *
 * Patrz docs/adr/0006-transport-wstrzykiwany-do-klienta-api.md
 */
export function configureWebApi(): void {
  configureApi({
    app: async <TData>(url: string, options: RequestInit = {}) => {
      return (await webRequest<unknown>(url, options)) as TData;
    },

    // Allauth traktuje 401 i 410 jako normalną część protokołu sesji, nie jako
    // błąd — tak samo jak po stronie mobilnej.
    auth: async <TData>(url: string, options: RequestInit = {}) => {
      return (await webRequest<unknown>(url, options, {
        acceptAllStatuses: true,
      })) as TData;
    },
  });
}
