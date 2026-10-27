import { z } from "zod";
import { PostAllauthClientV1AuthSignupBody } from "@olivin/api/generated/auth/authentication-account/authentication-account.zod";
import type { SignupBody } from "@olivin/api/generated/auth/schemas/signupBody";

// Reguły zgodne z profilem (`apps/accounts/usernames.py`) — ten sam kształt
// nazwy wybiera klient na webie i mobile.
export const USERNAME_MIN_LENGTH = 3;
export const USERNAME_MAX_LENGTH = 30;
const USERNAME_PATTERN = /^[A-Za-z0-9._-]+$/;
export const PASSWORD_MIN_LENGTH = 8;

/** Reguły nazwy konta wspólne dla rejestracji e-mailem i provider signup. */
export const usernameSchema = z
  .string()
  .trim()
  .min(USERNAME_MIN_LENGTH, "username_too_short")
  .max(USERNAME_MAX_LENGTH, "username_too_long")
  .regex(USERNAME_PATTERN, "username_invalid");

/**
 * Zgody przy zakładaniu konta — wspólne dla rejestracji e-mailem
 * i dokończenia rejestracji po Google/Facebook (#351).
 */
export const signupConsentsSchema = z.object({
  consentTerms: z.literal(true, "consent_required"),
  consentPrivacy: z.literal(true, "consent_required"),
  consentMarketing: z.boolean(),
});

export type SignupConsentsValues = {
  consentTerms: boolean;
  consentPrivacy: boolean;
  consentMarketing: boolean;
};

export const NO_SIGNUP_CONSENTS: SignupConsentsValues = {
  consentTerms: false,
  consentPrivacy: false,
  consentMarketing: false,
};

/**
 * Schemat formularza rejestracji e-mailem.
 *
 * Wysyłany ładunek waliduje schemat zod wygenerowany przez Orvala
 * (`assertSignupBody`) — zmiana pola w allauth wyjdzie w testach, zamiast
 * cicho zniknąć w żądaniu.
 */
export const registerFormSchema = z
  .object({
    email: z.email("email_invalid"),
    username: usernameSchema,
    password: z.string().min(PASSWORD_MIN_LENGTH, "password_too_short"),
    passwordConfirm: z.string().min(1, "password_confirm_required"),
  })
  .extend(signupConsentsSchema.shape)
  .refine((value) => value.password === value.passwordConfirm, {
    message: "password_mismatch",
    path: ["passwordConfirm"],
  });

export type RegisterFormValues = z.infer<typeof registerFormSchema>;

/**
 * Wartości formularza przed walidacją: zgody są boolowskie, bo startują jako
 * niezaznaczone. Dopiero schemat wymusza `true` przy wymaganych zgodach.
 */
export type RegisterFormInput = Omit<
  z.input<typeof registerFormSchema>,
  keyof SignupConsentsValues
> &
  SignupConsentsValues;

/**
 * Zamienia wartości formularza na ciało żądania allauth (`consent_*`).
 *
 * `preferred_language` pomijamy: backend bierze język maili z `Accept-Language`
 * ustawianego przez warstwę transportu.
 */
export function toSignupBody(values: RegisterFormValues): SignupBody {
  return {
    email: values.email,
    username: values.username,
    password: values.password,
    consent_terms: values.consentTerms,
    consent_privacy: values.consentPrivacy,
    consent_marketing: values.consentMarketing,
  };
}

/** Sprawdza ładunek schematem wygenerowanym z API allauth. */
export function assertSignupBody(body: SignupBody) {
  return PostAllauthClientV1AuthSignupBody.parse(body);
}
