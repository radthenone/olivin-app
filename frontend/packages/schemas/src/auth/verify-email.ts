import { z } from "zod";
import { PostAllauthClientV1AuthEmailVerifyBody } from "@olivin/api/generated/auth/authentication-account/authentication-account.zod";
import type { VerifyEmailBody } from "@olivin/api/generated/auth/schemas/verifyEmailBody";

/**
 * Schemat weryfikacji e-maila kodem z wiadomości.
 *
 * Bierzemy kształt z zod wygenerowanego przez Orvala i dokładamy tylko regułę,
 * że kod nie może być pusty.
 */
export const verifyEmailFormSchema =
  PostAllauthClientV1AuthEmailVerifyBody.extend({
    key: z.string().trim().min(1, "code_required"),
  });

export type VerifyEmailFormValues = z.infer<typeof verifyEmailFormSchema>;

export function toVerifyEmailBody(
  values: VerifyEmailFormValues,
): VerifyEmailBody {
  return { key: values.key };
}
