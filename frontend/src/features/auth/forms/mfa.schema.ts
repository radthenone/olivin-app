import { z } from "zod";

/**
 * Schemat formularza kodu MFA.
 */
export const mfaSchema = z.object({
  code: z.string().min(6, "Podaj kod z aplikacji uwierzytelniającej."),
});

export type MfaFormValues = z.infer<typeof mfaSchema>;
