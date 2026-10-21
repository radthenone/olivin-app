import { describe, expect, test } from "bun:test";

import {
  NO_SIGNUP_CONSENTS,
  assertSignupBody,
  registerFormSchema,
  toSignupBody,
} from "./register";

const validValues = {
  email: "jan@example.com",
  username: "jan_kowalski",
  password: "tajne-haslo",
  passwordConfirm: "tajne-haslo",
  consentTerms: true,
  consentPrivacy: true,
  consentMarketing: false,
};

function issuePaths(values: unknown): string[] {
  const parsed = registerFormSchema.safeParse(values);
  return parsed.success
    ? []
    : parsed.error.issues.map((issue) => String(issue.path[0]));
}

describe("registerFormSchema", () => {
  test("accepts a complete form with required consents", () => {
    const parsed = registerFormSchema.safeParse(validValues);

    expect(parsed.success).toBe(true);
  });

  test("requires the terms and privacy consents", () => {
    expect(issuePaths(validValues)).toEqual([]);

    expect(issuePaths({ ...validValues, consentTerms: false })).toContain(
      "consentTerms",
    );
    expect(issuePaths({ ...validValues, consentPrivacy: false })).toContain(
      "consentPrivacy",
    );
  });

  test("keeps marketing consent optional", () => {
    expect(
      registerFormSchema.safeParse({
        ...validValues,
        consentMarketing: false,
      }).success,
    ).toBe(true);
    expect(
      registerFormSchema.safeParse({
        ...validValues,
        consentMarketing: true,
      }).success,
    ).toBe(true);
  });

  test("rejects a taken-by-format username and short passwords", () => {
    expect(issuePaths({ ...validValues, username: "a" })).toContain("username");
    expect(issuePaths({ ...validValues, username: "jan kowalski" })).toContain(
      "username",
    );
    expect(
      issuePaths({
        ...validValues,
        password: "krotkie",
        passwordConfirm: "krotkie",
      }),
    ).toContain("password");
  });

  test("reports mismatched passwords on the confirmation field", () => {
    expect(
      issuePaths({ ...validValues, passwordConfirm: "inne-haslo" }),
    ).toContain("passwordConfirm");
  });

  test("starts with no consent accepted", () => {
    expect(NO_SIGNUP_CONSENTS).toEqual({
      consentTerms: false,
      consentPrivacy: false,
      consentMarketing: false,
    });
  });
});

describe("toSignupBody", () => {
  test("maps form values to allauth consent fields", () => {
    const parsed = registerFormSchema.parse(validValues);
    const body = toSignupBody(parsed);

    expect(body).toEqual({
      email: "jan@example.com",
      username: "jan_kowalski",
      password: "tajne-haslo",
      consent_terms: true,
      consent_privacy: true,
      consent_marketing: false,
    });
  });

  test("produces a payload accepted by the generated zod schema", () => {
    const parsed = registerFormSchema.parse(validValues);
    const body = toSignupBody(parsed);

    expect(() => assertSignupBody(body)).not.toThrow();
  });
});
