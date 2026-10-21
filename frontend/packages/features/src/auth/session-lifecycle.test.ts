import { afterEach, describe, expect, test } from "bun:test";
import type { HttpResponse } from "@olivin/api";

import {
  configureAuth,
  resetAuth,
  type SessionTokenStorage,
} from "./auth-config";
import { handleAllauthSessionLifecycle } from "./session-lifecycle";

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

function response(status: number, body: unknown): HttpResponse<unknown> {
  return { status, data: body, headers: new Headers() };
}

function allauthBody(sessionToken?: string) {
  return {
    status: 200,
    data: { flows: [] },
    meta: {
      is_authenticated: true,
      session_token: sessionToken,
    },
  };
}

/**
 * Token sesji allauth żyje w secure store na urządzeniu (#350), więc cykl
 * życia odpowiedzi musi pisać przez adapter, nie przez API platformy.
 */
describe("handleAllauthSessionLifecycle", () => {
  afterEach(() => {
    resetAuth();
  });

  test("zapisuje nowy token sesji z metadanych odpowiedzi", async () => {
    const storage = memoryStorage();
    configureAuth({ client: "app", sessionTokenStorage: storage });

    await handleAllauthSessionLifecycle(
      response(200, allauthBody("nowy-token")),
    );

    expect(storage.value).toBe("nowy-token");
  });

  test("usuwa token, gdy backend zgłasza wygasłą sesję", async () => {
    const storage = memoryStorage();
    storage.value = "stary-token";
    configureAuth({ client: "app", sessionTokenStorage: storage });

    await handleAllauthSessionLifecycle(response(410, { status: 410 }));

    expect(storage.value).toBeNull();
  });

  test("nie dotyka magazynu w trybie przeglądarkowym", async () => {
    const storage = memoryStorage();
    configureAuth({ client: "browser", sessionTokenStorage: storage });

    await handleAllauthSessionLifecycle(
      response(200, allauthBody("token-z-ciasteczka")),
    );

    expect(storage.value).toBeNull();
  });

  test("pomija odpowiedź, która nie jest ciałem allauth", async () => {
    const storage = memoryStorage();
    configureAuth({ client: "app", sessionTokenStorage: storage });

    await handleAllauthSessionLifecycle(response(200, { ok: true }));

    expect(storage.value).toBeNull();
  });
});
