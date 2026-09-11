import { z } from "zod";
import { adultDateOfBirthSchema } from "@features/account/forms/date-of-birth.schema";

/**
 * Schemat formularza rejestracji.
 */
export const registerSchema = z
  .object({
    email: z.email("Podaj poprawny adres email."),
    firstName: z.string().trim().min(1, "Podaj imię."),
    lastName: z.string().trim().min(1, "Podaj nazwisko."),
    dateOfBirth: adultDateOfBirthSchema,
    phoneNumber: z.string().trim().min(6, "Podaj numer telefonu."),
    password: z.string().min(8, "Hasło musi mieć co najmniej 8 znaków."),
    passwordConfirm: z.string().min(1, "Powtórz hasło."),
  })
  .refine((value) => value.password === value.passwordConfirm, {
    message: "Hasła muszą być takie same.",
    path: ["passwordConfirm"],
  });

export type RegisterFormValues = z.infer<typeof registerSchema>;
