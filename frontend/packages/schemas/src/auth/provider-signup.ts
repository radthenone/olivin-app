import { z } from "zod";

import { PostAllauthClientV1AuthProviderSignupBody } from "@olivin/api/generated/auth/authentication-providers/authentication-providers.zod";
import type { ProviderSignupBody } from "@olivin/api/generated/auth/schemas/providerSignupBody";

import {
  signupConsentsSchema,
  usernameSchema,
  type SignupConsentsValues,
} from "./register";

/**
 * Dokończenie rejestracji po Google/Facebook (#355).
 *
 * E-mail pochodzi z konta dostawcy i nie jest już pytany. Klient wybiera tylko
 * nazwę użytkownika i przechodzi te same zgody co przy rejestracji e-mailem.
 */
export const providerSignupFormSchema = z
  .object({ username: usernameSchema })
  .extend(signupConsentsSchema.shape);

export type ProviderSignupFormValues = z.infer<
  typeof providerSignupFormSchema
>;

/** Wartości formularza przed walidacją — zgody startują jako niezaznaczone. */
export type ProviderSignupFormInput = {
  username: string;
} & SignupConsentsValues;

/**
 * Zamienia formularz i e-mail dostawcy na ciało żądania allauth.
 */
export function toProviderSignupBody(
  email: string,
  values: ProviderSignupFormValues,
): ProviderSignupBody {
  return {
    email,
    username: values.username,
    consent_terms: values.consentTerms,
    consent_privacy: values.consentPrivacy,
    consent_marketing: values.consentMarketing,
  };
}

/** Sprawdza ładunek schematem wygenerowanym z API allauth. */
export function assertProviderSignupBody(body: ProviderSignupBody) {
  return PostAllauthClientV1AuthProviderSignupBody.parse(body);
}
