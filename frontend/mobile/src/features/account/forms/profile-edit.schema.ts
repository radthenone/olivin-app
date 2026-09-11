import { z } from "zod";

/**
 * Schemat edycji profilu dla pól, które użytkownik może zmienić samodzielnie.
 */
export const profileEditSchema = z.object({
  firstName: z.string().trim().min(1, "Podaj imię."),
  lastName: z.string().trim().min(1, "Podaj nazwisko."),
  phoneNumber: z.string().trim().min(6, "Podaj numer telefonu."),
});

export type ProfileEditFormValues = z.infer<typeof profileEditSchema>;
