import { describe, expect, test } from "bun:test";

import {
  PostAllauthClientV1AuthCodeConfirmBody,
  PostAllauthClientV1AuthCodeRequestBody,
} from "@olivin/api/generated/auth/authentication-login-by-code/authentication-login-by-code.zod";

import {
  confirmLoginCodeFormSchema,
  requestLoginCodeFormSchema,
  toConfirmLoginCodeBody,
  toRequestLoginCodeBody,
} from "./login-code";

/**
 * Schematy logowania jednorazowym kodem (#352).
 *
 * Reguły formularza żyją w pakiecie współdzielonym, a wysyłany ładunek
 * przechodzi przez schemat zod wygenerowany przez Orvala — zmiana pola
 * w allauth wyjdzie w testach, zamiast cicho zniknąć w żądaniu.
 */
describe("requestLoginCodeFormSchema", () => {
  test("accepts a valid email address", () => {
    const parsed = requestLoginCodeFormSchema.safeParse({
      email: "jan@example.com",
    });

    expect(parsed.success).toBe(true);
  });

  test("rejects an empty or malformed email address", () => {
    expect(requestLoginCodeFormSchema.safeParse({ email: "" }).success).toBe(
      false,
    );
    expect(requestLoginCodeFormSchema.safeParse({ email: "jan" }).success).toBe(
      false,
    );
  });

  test("reports an empty email as required and a malformed one as invalid", () => {
    const empty = requestLoginCodeFormSchema.safeParse({ email: "" });
    const malformed = requestLoginCodeFormSchema.safeParse({ email: "jan" });

    expect(empty.error?.issues[0]?.message).toBe("email_required");
    expect(malformed.error?.issues[0]?.message).toBe("email_invalid");
  });

  test("matches the generated allauth request-login-code body", () => {
    const body = toRequestLoginCodeBody(
      requestLoginCodeFormSchema.parse({ email: "jan@example.com" }),
    );

    expect(PostAllauthClientV1AuthCodeRequestBody.safeParse(body).success).toBe(
      true,
    );
  });

  test("rejects a phone-only payload, because the backend has no phone login", () => {
    const result = requestLoginCodeFormSchema.safeParse({
      phone: "+48123456789",
    });

    if (result.success) {
      throw new Error("phone-only payload must be rejected");
    }

    expect(result.error.issues[0]?.path).toEqual(["email"]);
  });

  test("reports the email_invalid code instead of prose", () => {
    const result = requestLoginCodeFormSchema.safeParse({ email: "jan" });

    if (result.success) {
      throw new Error("malformed email must be rejected");
    }

    expect(result.error.issues[0]?.message).toBe("email_invalid");
  });
});

describe("confirmLoginCodeFormSchema", () => {
  test("accepts a code and trims surrounding whitespace", () => {
    const parsed = confirmLoginCodeFormSchema.parse({ code: " ABC123 " });

    expect(parsed.code).toBe("ABC123");
  });

  test("rejects an empty or whitespace-only code", () => {
    expect(confirmLoginCodeFormSchema.safeParse({ code: "" }).success).toBe(
      false,
    );
    expect(confirmLoginCodeFormSchema.safeParse({ code: "   " }).success).toBe(
      false,
    );
  });

  test("matches the generated allauth confirm-login-code body", () => {
    const body = toConfirmLoginCodeBody(
      confirmLoginCodeFormSchema.parse({ code: "ABC123" }),
    );

    expect(PostAllauthClientV1AuthCodeConfirmBody.safeParse(body).success).toBe(
      true,
    );
  });

  test("reports the code_required code instead of prose", () => {
    const result = confirmLoginCodeFormSchema.safeParse({ code: "   " });

    if (result.success) {
      throw new Error("blank code must be rejected");
    }

    expect(result.error.issues[0]?.message).toBe("code_required");
  });

  test("leaves the code length to the backend", () => {
    expect(
      confirmLoginCodeFormSchema.safeParse({ code: "12345" }).success,
    ).toBe(true);
  });
});
