import { z } from "zod";
import { PostAllauthClientV1AuthCodeConfirmBody } from "@olivin/api/generated/auth/authentication-login-by-code/authentication-login-by-code.zod";
import type { ConfirmLoginCodeBody } from "@olivin/api/generated/auth/schemas/confirmLoginCodeBody";
import type { RequestLoginCodeBody } from "@olivin/api/generated/auth/schemas/requestLoginCodeBody";

/** Ładunek zamówienia kodu w wariancie e-mail. */
export type RequestLoginCodeEmailBody = Extract<
  RequestLoginCodeBody,
  { email: string }
>;

/**
 * Schemat zamówienia jednorazowego kodu logowania (#352, #405).
 *
 * Allauth opisuje ciało żądania jako unię e-mail/telefon, ale ten backend nie
 * ma skonfigurowanego logowania kodem na telefon (brak weryfikacji numeru),
 * a żaden ekran nie zbiera numeru — używamy wyłącznie wariantu e-mail i tylko
 * jego walidują formularze web i mobile. Dlatego wariant telefoniczny nie
 * trafia do pakietu współdzielonego.
 *
 * Schemat pola zostaje ręczny, mimo ADR 0033: wygenerowana unia sprawdza tylko
 * obecność `email`, bez formatu, a formularz musi odrzucić zły adres, zanim
 * poleci żądanie. Zgodność ładunku z Orvalem pilnuje `toRequestLoginCodeBody`
 * oraz testy zgodności.
 */
export const requestLoginCodeFormSchema = z.object({
  email: z.string().min(1, "email_required").pipe(z.email("email_invalid")),
});

export type RequestLoginCodeFormValues = z.infer<
  typeof requestLoginCodeFormSchema
>;

export function toRequestLoginCodeBody(
  values: RequestLoginCodeFormValues,
): RequestLoginCodeEmailBody {
  return { email: values.email };
}

/**
 * Schemat potwierdzenia kodu logowania (#352, #405).
 *
 * Wracamy z kształtu wygenerowanego przez Orvala i wymuszamy niepusty kod.
 * Długości i znaków kodu nie sprawdzamy po stronie klienta — zna je backend,
 * a jedna reguła obowiązuje web i mobile.
 */
export const confirmLoginCodeFormSchema =
  PostAllauthClientV1AuthCodeConfirmBody.extend({
    code: z.string().trim().min(1, "code_required"),
  });

export type ConfirmLoginCodeFormValues = z.infer<
  typeof confirmLoginCodeFormSchema
>;

export function toConfirmLoginCodeBody(
  values: ConfirmLoginCodeFormValues,
): ConfirmLoginCodeBody {
  return { code: values.code };
}
