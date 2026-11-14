import { describe, expect, test } from "bun:test";

import {
  assertProviderSignupBody,
  providerSignupFormSchema,
  toProviderSignupBody,
} from "./provider-signup";

const validValues = {
  username: "jan_google",
  consentTerms: true,
  consentPrivacy: true,
  consentMarketing: false,
};

function issuePaths(values: unknown): string[] {
  const parsed = providerSignupFormSchema.safeParse(values);
  return parsed.success
    ? []
    : parsed.error.issues.map((issue) => String(issue.path[0]));
}

describe("providerSignupFormSchema", () => {
  test("accepts a username with the required consents", () => {
    expect(providerSignupFormSchema.safeParse(validValues).success).toBe(true);
  });

  test("requires the terms and privacy consents", () => {
    expect(issuePaths({ ...validValues, consentTerms: false })).toContain(
      "consentTerms",
    );
    expect(issuePaths({ ...validValues, consentPrivacy: false })).toContain(
      "consentPrivacy",
    );
  });

  test("keeps marketing consent optional", () => {
    expect(
      providerSignupFormSchema.safeParse({
        ...validValues,
        consentMarketing: false,
      }).success,
    ).toBe(true);
    expect(
      providerSignupFormSchema.safeParse({
        ...validValues,
        consentMarketing: true,
      }).success,
    ).toBe(true);
  });

  test("rejects a username outside the account rules", () => {
    expect(issuePaths({ ...validValues, username: "a" })).toContain("username");
    expect(issuePaths({ ...validValues, username: "jan google" })).toContain(
      "username",
    );
  });
});

describe("toProviderSignupBody", () => {
  test("maps form values and the provider email onto allauth fields", () => {
    const parsed = providerSignupFormSchema.parse(validValues);

    expect(toProviderSignupBody("jan@example.com", parsed)).toEqual({
      email: "jan@example.com",
      username: "jan_google",
      consent_terms: true,
      consent_privacy: true,
      consent_marketing: false,
    });
  });

  test("produces a payload accepted by the generated zod schema", () => {
    const parsed = providerSignupFormSchema.parse(validValues);
    const body = toProviderSignupBody("jan@example.com", parsed);

    expect(() => assertProviderSignupBody(body)).not.toThrow();
  });
});
