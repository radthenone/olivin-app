import { z } from "zod";
import { adultDateOfBirthSchema } from "./date-of-birth.schema";

/**
 * Schemat minimalnych danych profilu wymaganych przez konto klienta.
 */
export const profileRequiredSchema = z.object({
  firstName: z.string().trim().min(1, "Podaj imię."),
  lastName: z.string().trim().min(1, "Podaj nazwisko."),
  dateOfBirth: adultDateOfBirthSchema,
  phoneNumber: z.string().trim().min(6, "Podaj numer telefonu."),
});

export type ProfileRequiredFormValues = z.infer<typeof profileRequiredSchema>;
