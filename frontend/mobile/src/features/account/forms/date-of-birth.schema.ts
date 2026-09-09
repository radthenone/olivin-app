import { z } from "zod";

function isAdult(value: string) {
  const [yearValue, monthValue, dayValue] = value.split("-").map(Number);
  const birthDate = new Date(yearValue, monthValue - 1, dayValue);

  if (
    Number.isNaN(birthDate.getTime()) ||
    birthDate.getFullYear() !== yearValue ||
    birthDate.getMonth() !== monthValue - 1 ||
    birthDate.getDate() !== dayValue
  ) {
    return false;
  }

  const today = new Date();
  const adultBirthDate = new Date(
    today.getFullYear() - 18,
    today.getMonth(),
    today.getDate(),
  );

  return birthDate <= adultBirthDate;
}

/**
 * Schemat daty urodzenia klienta uprawnionego do zakupów.
 */
export const adultDateOfBirthSchema = z
  .string()
  .trim()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "Podaj datę w formacie RRRR-MM-DD.")
  .refine(isAdult, "Musisz mieć ukończone 18 lat.");
