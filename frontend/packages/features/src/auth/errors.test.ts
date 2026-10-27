import { describe, expect, test } from "bun:test";

import {
  mapMfaErrors,
  mapPasswordResetErrors,
  mapSignupErrors,
  mapVerifyEmailErrors,
} from "./errors";

describe("mapSignupErrors", () => {
  test("maps backend fields onto form fields", () => {
    const errors = mapSignupErrors({
      status: 400,
      errors: [
        { param: "username", code: "username_taken", message: "Taken" },
        { param: "password", code: "password_too_short", message: "Short" },
        { param: "consent_terms", code: "required", message: "Required" },
        { param: "email", code: "invalid", message: "Invalid" },
      ],
    });

    expect(errors.map((error) => error.target)).toEqual([
      "username",
      "password",
      "consentTerms",
      "email",
    ]);
    expect(errors.map((error) => error.code)).toEqual([
      "usernameTaken",
      "invalid",
      "consentRequired",
      "invalid",
    ]);
  });

  test("recognises a taken email even though the backend hides it", () => {
    const errors = mapSignupErrors({
      status: 400,
      errors: [{ param: "email", code: "email_taken" }],
    });

    expect(errors).toEqual([{ target: "email", code: "emailTaken" }]);
  });

  test("maps the signup rate limit", () => {
    const errors = mapSignupErrors({
      status: 429,
      errors: [{ code: "too_many_signup_attempts" }],
    });

    expect(errors).toEqual([{ target: "form", code: "tooManyAttempts" }]);
  });

  test("keeps the backend message next to a known code", () => {
    expect(
      mapSignupErrors({
        status: 400,
        errors: [
          {
            param: "consent_terms",
            code: "required",
            message: "To pole jest wymagane.",
          },
        ],
      }),
    ).toEqual([
      {
        target: "consentTerms",
        code: "consentRequired",
        message: "To pole jest wymagane.",
      },
    ]);
  });

  test("keeps an unknown error message and puts it on the form", () => {
    const errors = mapSignupErrors({
      status: 400,
      errors: [
        { param: "unknown", code: "consent_document_missing", message: "Brak" },
      ],
    });

    expect(errors).toEqual([
      { target: "form", code: "backend", message: "Brak" },
    ]);
  });

  test("falls back to a generic form error without an error list", () => {
    expect(mapSignupErrors({ status: 400 })).toEqual([
      { target: "form", code: "backend" },
    ]);
  });
});

describe("mapVerifyEmailErrors", () => {
  test("maps a wrong or expired code", () => {
    expect(
      mapVerifyEmailErrors({
        status: 400,
        errors: [{ param: "key", code: "invalid" }],
      }),
    ).toEqual([{ target: "form", code: "codeInvalid" }]);
  });

  test("keeps the backend message next to a wrong or expired code", () => {
    expect(
      mapVerifyEmailErrors({
        status: 400,
        errors: [
          { param: "key", code: "invalid", message: "Invalid or expired key." },
        ],
      }),
    ).toEqual([
      {
        target: "form",
        code: "codeInvalid",
        message: "Invalid or expired key.",
      },
    ]);
  });

  test("maps too many attempts", () => {
    expect(
      mapVerifyEmailErrors({
        status: 429,
        errors: [{ code: "too_many_confirm_email_attempts" }],
      }),
    ).toEqual([{ target: "form", code: "tooManyAttempts" }]);
  });

  test("falls back to a generic form error", () => {
    expect(mapVerifyEmailErrors({ status: 400 })).toEqual([
      { target: "form", code: "backend" },
    ]);
  });
});

describe("mapPasswordResetErrors", () => {
  test("maps a wrong or expired reset code onto the code field", () => {
    expect(
      mapPasswordResetErrors({
        status: 400,
        errors: [
          {
            param: "key",
            code: "token_invalid",
            message: "The password reset token was invalid.",
          },
        ],
      }),
    ).toEqual([
      {
        target: "key",
        code: "codeInvalid",
        message: "The password reset token was invalid.",
      },
    ]);
  });

  test("maps a malformed email onto the email field", () => {
    expect(
      mapPasswordResetErrors({
        status: 400,
        errors: [
          {
            param: "email",
            code: "invalid",
            message: "Enter a valid email address.",
          },
        ],
      }),
    ).toEqual([
      {
        target: "email",
        code: "backend",
        message: "Enter a valid email address.",
      },
    ]);
  });

  test("maps a password rejected by the backend onto the password field", () => {
    expect(
      mapPasswordResetErrors({
        status: 400,
        errors: [
          {
            param: "password",
            code: "password_too_short",
            message: "This password is too short.",
          },
        ],
      }),
    ).toEqual([
      {
        target: "password",
        code: "passwordInvalid",
        message: "This password is too short.",
      },
    ]);
  });

  test("maps the reset rate limit", () => {
    expect(
      mapPasswordResetErrors({
        status: 429,
        errors: [{ code: "too_many_password_reset_attempts" }],
      }),
    ).toEqual([{ target: "form", code: "tooManyAttempts" }]);
  });

  test("keeps an unknown error message on the form", () => {
    expect(
      mapPasswordResetErrors({
        status: 400,
        errors: [
          { param: "account", code: "unknown", message: "Coś poszło nie tak." },
        ],
      }),
    ).toEqual([
      { target: "form", code: "backend", message: "Coś poszło nie tak." },
    ]);
  });

  test("falls back to a generic form error without an error list", () => {
    expect(mapPasswordResetErrors({ status: 400 })).toEqual([
      { target: "form", code: "backend" },
    ]);
  });
});

describe("mapMfaErrors", () => {
  test("maps an incorrect authenticator code to the code field", () => {
    expect(
      mapMfaErrors({
        status: 400,
        errors: [
          { param: "code", code: "incorrect_code", message: "Incorrect code." },
        ],
      }),
    ).toEqual([
      { target: "code", code: "codeInvalid", message: "Incorrect code." },
    ]);
  });

  test("maps too many attempts to a readable form error", () => {
    expect(
      mapMfaErrors({
        status: 429,
        errors: [{ code: "too_many_attempts" }],
      }),
    ).toEqual([{ target: "form", code: "tooManyAttempts" }]);
  });

  test("keeps an unknown backend error with its message", () => {
    expect(
      mapMfaErrors({
        status: 400,
        errors: [{ code: "unexpected", message: "Something else." }],
      }),
    ).toEqual([
      { target: "form", code: "backend", message: "Something else." },
    ]);
  });

  test("falls back to a generic form error when the body has no errors", () => {
    expect(mapMfaErrors({ status: 400 })).toEqual([
      { target: "form", code: "backend" },
    ]);
  });
});
