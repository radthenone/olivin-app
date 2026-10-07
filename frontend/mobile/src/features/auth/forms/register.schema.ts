import { z } from "zod";
import { adultDateOfBirthSchema } from "@features/account/forms/date-of-birth.schema";

/**
 * Zgody przy zakładaniu konta — wspólne dla rejestracji e-mailem
 * i dokończenia rejestracji po Google/Facebook.
 */
export const signupConsentsSchema = z.object({
  consentTerms: z.literal(true, "Zaakceptuj regulamin."),
  consentPrivacy: z.literal(true, "Zaakceptuj politykę prywatności."),
  consentMarketing: z.boolean(),
});

export type SignupConsentsValues = {
  consentTerms: boolean;
  consentPrivacy: boolean;
  consentMarketing: boolean;
};

export const NO_CONSENTS: SignupConsentsValues = {
  consentTerms: false,
  consentPrivacy: false,
  consentMarketing: false,
};

/** Zgody w kształcie pól formularza allauth (`consent_*`). */
export function toSignupConsentsBody(values: SignupConsentsValues) {
  return {
    consent_terms: values.consentTerms,
    consent_privacy: values.consentPrivacy,
    consent_marketing: values.consentMarketing,
  };
}

/**
 * Schemat formularza rejestracji.
 */
export const registerSchema = z
  .object({
    email: z.email("Podaj poprawny adres email."),
    firstName: z.string().trim().min(1, "Podaj imię."),
    lastName: z.string().trim().min(1, "Podaj nazwisko."),
    dateOfBirth: adultDateOfBirthSchema,
    phoneNumber: z.string().trim().min(6, "Podaj numer telefonu."),
    password: z.string().min(8, "Hasło musi mieć co najmniej 8 znaków."),
    passwordConfirm: z.string().min(1, "Powtórz hasło."),
  })
  .extend(signupConsentsSchema.shape)
  .refine((value) => value.password === value.passwordConfirm, {
    message: "Hasła muszą być takie same.",
    path: ["passwordConfirm"],
  });

export type RegisterFormValues = z.infer<typeof registerSchema>;
