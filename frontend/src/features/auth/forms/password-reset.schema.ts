import { z } from "zod";

/**
 * Schemat formularza rozpoczęcia resetu hasła.
 */
export const passwordResetRequestSchema = z.object({
  email: z.email("Podaj poprawny adres email."),
});

/**
 * Schemat formularza ustawienia nowego hasła.
 */
export const passwordResetConfirmSchema = z.object({
  password: z.string().min(8, "Hasło musi mieć co najmniej 8 znaków."),
});

export type PasswordResetRequestFormValues = z.infer<
  typeof passwordResetRequestSchema
>;
export type PasswordResetConfirmFormValues = z.infer<
  typeof passwordResetConfirmSchema
>;
