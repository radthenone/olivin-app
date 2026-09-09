import { z } from "zod";

/**
 * Schemat formularza rozpoczęcia logowania kodem.
 */
export const requestLoginCodeSchema = z.object({
  email: z.email("Podaj poprawny adres email."),
});

/**
 * Schemat formularza potwierdzenia logowania kodem.
 */
export const confirmLoginCodeSchema = z.object({
  code: z.string().min(6, "Podaj kod logowania z wiadomości email."),
});

export type RequestLoginCodeFormValues = z.infer<typeof requestLoginCodeSchema>;
export type ConfirmLoginCodeFormValues = z.infer<typeof confirmLoginCodeSchema>;
