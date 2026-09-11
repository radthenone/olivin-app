import { z } from "zod";

/**
 * Schemat formularza logowania.
 *
 * Dlaczego istnieje:
 * walidacja wejścia należy do feature auth, a nie do komponentu ekranu.
 */
export const loginSchema = z.object({
  email: z.email("Podaj poprawny adres email."),
  password: z.string().min(1, "Podaj hasło."),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
