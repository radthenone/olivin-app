import { afterEach, describe, expect, test } from "bun:test";

import {
  configureAuth,
  getAuthClient,
  getSessionTokenStorage,
  resetAuth,
  type SessionTokenStorage,
} from "./auth-config";

function memoryStorage(): SessionTokenStorage & { value: string | null } {
  const storage = {
    value: null as string | null,
    async get() {
      return storage.value;
    },
    async set(value: string) {
      storage.value = value;
    },
    async remove() {
      storage.value = null;
    },
  };

  return storage;
}

/**
 * Platforma wnosi klienta allauth i magazyn tokena sesji przy starcie (#350),
 * tym samym wzorcem co transport API (ADR 0006, ADR 0033).
 */
describe("auth config", () => {
  afterEach(() => {
    resetAuth();
  });

  test("domyślnie działa w trybie przeglądarkowym bez magazynu tokena", async () => {
    expect(getAuthClient()).toBe("browser");

    const storage = getSessionTokenStorage();
    await storage.set("token");

    expect(await storage.get()).toBeNull();
  });

  test("przyjmuje klienta app i magazyn wstrzyknięty przez aplikację", async () => {
    const storage = memoryStorage();
    configureAuth({ client: "app", sessionTokenStorage: storage });

    expect(getAuthClient()).toBe("app");

    await getSessionTokenStorage().set("sesja-123");

    expect(await getSessionTokenStorage().get()).toBe("sesja-123");
    expect(storage.value).toBe("sesja-123");

    await getSessionTokenStorage().remove();

    expect(await getSessionTokenStorage().get()).toBeNull();
  });
});
