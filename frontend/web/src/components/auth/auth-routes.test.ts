import { describe, expect, test } from "bun:test";

import { authRoutes } from "./auth-routes";

/**
 * Trasy auth składa jedna mapa, a nie ręcznie sklejane ścieżki (#406).
 *
 * Każda trasa dostaje locale i zwraca gotową ścieżkę, więc formularze nie
 * powtarzają `/${locale}/...` ani castu na typ Route.
 */
describe("authRoutes", () => {
  test("builds the login code request and confirm paths for a locale", () => {
    expect(authRoutes.loginCode("pl")).toBe("/pl/login/code");
    expect(authRoutes.loginCodeConfirm("pl")).toBe("/pl/login/code/confirm");
  });

  test("builds the password login and home paths for a locale", () => {
    expect(authRoutes.login("en")).toBe("/en/login");
    expect(authRoutes.home("en")).toBe("/en");
  });

  test("builds the expired-login return path with the expired flag", () => {
    expect(authRoutes.loginCodeExpired("pl")).toBe("/pl/login/code?expired=1");
    expect(authRoutes.loginCodeExpired("pl", "code")).toBe(
      "/pl/login/code?expired=code",
    );
  });
});
