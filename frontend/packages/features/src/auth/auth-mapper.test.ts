import { describe, expect, test } from "bun:test";

import { mapAllauthBodyToAuthState } from "./auth-mapper";

const user = {
  id: 7,
  display: "Jan Jubiler",
  email: "jan@example.com",
  has_usable_password: true,
};

/**
 * Stan sesji dla routingu mobile (#350) — bez statusów HTTP allauth w UI.
 */
describe("mapAllauthBodyToAuthState", () => {
  test("zwraca zalogowanego użytkownika i flows", () => {
    const state = mapAllauthBodyToAuthState({
      status: 200,
      data: { user, flows: [{ id: "login" }] },
      meta: { is_authenticated: true },
    });

    expect(state).toEqual({
      status: "authenticated",
      user,
      flows: [{ id: "login" }],
    });
  });

  test("rozpoznaje wymagane MFA", () => {
    const state = mapAllauthBodyToAuthState({
      status: 401,
      data: { flows: [{ id: "mfa_authenticate" }] },
      meta: { is_authenticated: false },
    });

    expect(state).toEqual({
      status: "mfa_required",
      flows: [{ id: "mfa_authenticate" }],
    });
  });

  test("rozpoznaje wymaganą weryfikację email", () => {
    const state = mapAllauthBodyToAuthState({
      status: 401,
      data: { flows: [{ id: "verify_email" }] },
      meta: { is_authenticated: false },
    });

    expect(state.status).toBe("email_verification_required");
  });

  test("rozpoznaje niedokończoną rejestrację providera", () => {
    const state = mapAllauthBodyToAuthState({
      status: 401,
      data: { flows: [{ id: "provider_signup", is_pending: true }] },
      meta: { is_authenticated: false },
    });

    expect(state.status).toBe("provider_signup_required");
  });

  test("nieznane ciało traktuje jak brak sesji", () => {
    expect(mapAllauthBodyToAuthState({ ok: true })).toEqual({
      status: "unauthenticated",
      flows: [],
    });
  });
});
