import { z } from "zod";
import { PostAllauthClientV1AuthPasswordResetBody } from "@olivin/api/generated/auth/authentication-password-reset/authentication-password-reset.zod";
import type { RequestPasswordBody } from "@olivin/api/generated/auth/schemas/requestPasswordBody";
import type { ResetPasswordBody } from "@olivin/api/generated/auth/schemas/resetPasswordBody";

import { PASSWORD_MIN_LENGTH } from "./register";

/**
 * Schemat prośby o reset hasła (#353).
 *
 * Formularz webowy wysyła wyłącznie adres e-mail. Allauth przy włączonym
 * resecie kodem trzyma oczekujący etap w sesji, więc ekran potwierdzenia nie
 * potrzebuje adresu w URL.
 */
export const passwordResetRequestFormSchema = z.object({
  email: z.email("email_invalid"),
});

export type PasswordResetRequestFormValues = z.infer<
  typeof passwordResetRequestFormSchema
>;

export function toPasswordResetRequestBody(
  values: PasswordResetRequestFormValues,
): RequestPasswordBody {
  return { email: values.email };
}

/**
 * Schemat ustawienia nowego hasła kodem z maila (#353).
 *
 * Kształt bierzemy z Orvala, a wymagania hasła są wspólne z rejestracją —
 * backend i tak waliduje je ponownie.
 */
export const passwordResetConfirmFormSchema =
  PostAllauthClientV1AuthPasswordResetBody.extend({
    key: z.string().trim().min(1, "code_required"),
    password: z.string().min(PASSWORD_MIN_LENGTH, "password_too_short"),
  });

export type PasswordResetConfirmFormValues = z.infer<
  typeof passwordResetConfirmFormSchema
>;

export function toPasswordResetConfirmBody(
  values: PasswordResetConfirmFormValues,
): ResetPasswordBody {
  return { key: values.key, password: values.password };
}
