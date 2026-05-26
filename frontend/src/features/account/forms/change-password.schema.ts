import { z } from "zod";

/**
 * Schemat formularza zmiany hasła zalogowanego użytkownika.
 */
export const changePasswordSchema = z.object({
  currentPassword: z.string().optional(),
  newPassword: z.string().min(8, "Nowe hasło musi mieć co najmniej 8 znaków."),
});

export type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;
