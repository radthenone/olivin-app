import { z } from "zod";
import { PostAllauthClientV1AuthCodeConfirmBody } from "@olivin/api/generated/auth/authentication-login-by-code/authentication-login-by-code.zod";
import type { ConfirmLoginCodeBody } from "@olivin/api/generated/auth/schemas/confirmLoginCodeBody";
import type { RequestLoginCodeBody } from "@olivin/api/generated/auth/schemas/requestLoginCodeBody";

/**
 * Schemat zamówienia jednorazowego kodu logowania (#352).
 *
 * Formularz webowy wysyła wyłącznie adres e-mail — wariant telefoniczny
 * należy do aplikacji mobilnej.
 */
export const requestLoginCodeFormSchema = z.object({
  email: z.email("email_invalid"),
});

export type RequestLoginCodeFormValues = z.infer<
  typeof requestLoginCodeFormSchema
>;

export function toRequestLoginCodeBody(
  values: RequestLoginCodeFormValues,
): Extract<RequestLoginCodeBody, { email: string }> {
  return { email: values.email };
}

/**
 * Schemat potwierdzenia kodu logowania (#352).
 *
 * Wracamy z kształtu wygenerowanego przez Orvala i wymuszamy niepusty kod —
 * resztę reguł (długość, znaki) zna backend.
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
