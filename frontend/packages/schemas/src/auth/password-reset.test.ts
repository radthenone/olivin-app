import { describe, expect, test } from "bun:test";

import {
  PostAllauthClientV1AuthPasswordRequestBody,
  PostAllauthClientV1AuthPasswordResetBody,
} from "@olivin/api/generated/auth/authentication-password-reset/authentication-password-reset.zod";

import {
  passwordResetConfirmFormSchema,
  passwordResetRequestFormSchema,
  toPasswordResetConfirmBody,
  toPasswordResetRequestBody,
} from "./password-reset";

/**
 * Schematy resetu hasła kodem (#353).
 *
 * Reguły formularza żyją w pakiecie współdzielonym, a wysyłany ładunek
 * przechodzi przez schemat zod wygenerowany przez Orvala — zmiana pola
 * w allauth wyjdzie w testach, zamiast cicho zniknąć w żądaniu.
 */
describe("passwordResetRequestFormSchema", () => {
  test("accepts a valid email address", () => {
    const parsed = passwordResetRequestFormSchema.safeParse({
      email: "jan@example.com",
    });

    expect(parsed.success).toBe(true);
  });

  test("rejects an empty or malformed email address", () => {
    expect(
      passwordResetRequestFormSchema.safeParse({ email: "" }).success,
    ).toBe(false);
    expect(
      passwordResetRequestFormSchema.safeParse({ email: "jan" }).success,
    ).toBe(false);
  });

  test("matches the generated allauth password-request body", () => {
    const body = toPasswordResetRequestBody(
      passwordResetRequestFormSchema.parse({ email: "jan@example.com" }),
    );

    expect(
      PostAllauthClientV1AuthPasswordRequestBody.safeParse(body).success,
    ).toBe(true);
  });
});

describe("passwordResetConfirmFormSchema", () => {
  test("accepts a code and a password meeting the minimum length", () => {
    const parsed = passwordResetConfirmFormSchema.parse({
      key: " ABC123 ",
      password: "nowe-haslo-123",
    });

    expect(parsed.key).toBe("ABC123");
  });

  test("rejects an empty code and a password that is too short", () => {
    const emptyCode = passwordResetConfirmFormSchema.safeParse({
      key: "   ",
      password: "nowe-haslo-123",
    });
    const shortPassword = passwordResetConfirmFormSchema.safeParse({
      key: "ABC123",
      password: "krotkie",
    });

    expect(emptyCode.success).toBe(false);
    expect(shortPassword.success).toBe(false);
  });

  test("matches the generated allauth password-reset body", () => {
    const body = toPasswordResetConfirmBody(
      passwordResetConfirmFormSchema.parse({
        key: "ABC123",
        password: "nowe-haslo-123",
      }),
    );

    expect(
      PostAllauthClientV1AuthPasswordResetBody.safeParse(body).success,
    ).toBe(true);
  });
});
