import { describe, expect, test } from "bun:test";

import { PostAllauthClientV1AuthEmailVerifyBody } from "@olivin/api/generated/auth/authentication-account/authentication-account.zod";

import { toVerifyEmailBody, verifyEmailFormSchema } from "./verify-email";

describe("verifyEmailFormSchema", () => {
  test("accepts a non-empty code", () => {
    const parsed = verifyEmailFormSchema.safeParse({ key: "ABC123" });

    expect(parsed.success).toBe(true);
  });

  test("rejects an empty or whitespace-only code", () => {
    expect(verifyEmailFormSchema.safeParse({ key: "" }).success).toBe(false);
    expect(verifyEmailFormSchema.safeParse({ key: "   " }).success).toBe(false);
  });

  test("matches the generated allauth verify-email body", () => {
    const body = toVerifyEmailBody(
      verifyEmailFormSchema.parse({ key: "ABC123" }),
    );

    expect(PostAllauthClientV1AuthEmailVerifyBody.safeParse(body).success).toBe(
      true,
    );
  });
});
