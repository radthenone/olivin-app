// Kontrakt transportu.
//
// Pakiet zna wszystkie endpointy, typy i hooki zapytań, ale nie wie, czym
// wykonać żądanie — bo to różni się między celami: aplikacja mobilna wysyła
// nagłówek z tokenem sesji odczytanym z bezpiecznego magazynu urządzenia, a
// web wysyła ciasteczka wraz z tokenem zabezpieczającym przed fałszowaniem
// żądań. Aplikacja wstrzykuje swoją implementację przy starcie.
//
// Patrz docs/adr/0006-transport-wstrzykiwany-do-klienta-api.md

/**
 * Wykonuje pojedyncze żądanie i zwraca odpowiedź już rozpakowaną do danych.
 * Sygnatura odpowiada temu, czego oczekuje kod generowany przez Orval.
 */
export type ApiFetcher = <TData>(
  url: string,
  options?: RequestInit,
) => Promise<TData>;

export interface ApiTransport {
  /** Endpointy domenowe DRF pod prefiksem wersji API. */
  app: ApiFetcher;
  /** Endpointy sesji allauth — osobny schemat i osobny cykl życia. */
  auth: ApiFetcher;
}

let transport: ApiTransport | null = null;

/**
 * Podłącza implementację transportu. Wywoływane raz, przy starcie aplikacji,
 * zanim wykonane zostanie jakiekolwiek żądanie.
 */
export function configureApi(next: ApiTransport): void {
  transport = next;
}

/** Odpina transport. Przydatne w testach, żeby nie przeciekał między nimi. */
export function resetApi(): void {
  transport = null;
}

function requireTransport(): ApiTransport {
  if (!transport) {
    throw new Error(
      "Transport API nie został skonfigurowany. Wywołaj configureApi() przy " +
        "starcie aplikacji, zanim wykonasz pierwsze żądanie.",
    );
  }

  return transport;
}

export function appFetch<TData>(
  url: string,
  options?: RequestInit,
): Promise<TData> {
  return requireTransport().app<TData>(url, options);
}

export function authFetch<TData>(
  url: string,
  options?: RequestInit,
): Promise<TData> {
  return requireTransport().auth<TData>(url, options);
}
