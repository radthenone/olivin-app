/**
 * Konfiguracja platformowa wspólnych hooków auth.
 *
 * Wzorzec jak transport API z ADR 0006: pakiet zna flow allauth, ale nie wie,
 * którym klientem rozmawiać ani gdzie trzymać token sesji. Aplikacja wstrzykuje
 * jedno i drugie przy starcie, zanim wykona pierwsze żądanie.
 *
 * Patrz docs/adr/0033-hooki-orvala-wprost-logika-domeny-w-pakiecie-features.md
 */

export type AuthClient = "app" | "browser";

/**
 * Magazyn tokena sesji allauth dla klienta `app`.
 *
 * Web trzyma sesję w ciasteczkach, więc domyślnie nic nie zapisuje. Mobile
 * dostarcza adapter na `expo-secure-store`.
 */
export interface SessionTokenStorage {
  get(): Promise<string | null>;
  set(value: string): Promise<void>;
  remove(): Promise<void>;
}

export type AuthConfig = {
  client: AuthClient;
  sessionTokenStorage: SessionTokenStorage;
};

const noopSessionTokenStorage: SessionTokenStorage = {
  async get() {
    return null;
  },
  async set() {},
  async remove() {},
};

const defaultConfig = (): AuthConfig => ({
  client: "browser",
  sessionTokenStorage: noopSessionTokenStorage,
});

let config: AuthConfig = defaultConfig();

/**
 * Podłącza konfigurację auth. Wywoływane raz, przy starcie aplikacji.
 */
export function configureAuth(next: Partial<AuthConfig>): void {
  config = {
    client: next.client ?? config.client,
    sessionTokenStorage: next.sessionTokenStorage ?? config.sessionTokenStorage,
  };
}

/** Przywraca stan domyślny. Przydatne w testach, żeby config nie przeciekał. */
export function resetAuth(): void {
  config = defaultConfig();
}

export function getAuthClient(): AuthClient {
  return config.client;
}

export function getSessionTokenStorage(): SessionTokenStorage {
  return config.sessionTokenStorage;
}
