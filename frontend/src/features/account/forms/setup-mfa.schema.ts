import { z } from "zod";

/**
 * Schemat formularza aktywacji TOTP.
 */
export const setupMfaSchema = z.object({
  code: z.string().trim().min(6, "Podaj kod z aplikacji uwierzytelniającej."),
});

export type SetupMfaFormValues = z.infer<typeof setupMfaSchema>;
