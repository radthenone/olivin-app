import clsx_default, { type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Łączy klasy CSS/Tailwind przy użyciu clsx i tailwind-merge.
 * Rozwiązuje konflikty klas Tailwind CSS.
 *
 * @param inputs - Tablica wartości klas, obiektów lub warunków
 * @returns Zmergowany ciąg znaków z klasami
 */
export const cn = (...inputs: ClassValue[]): string => {
  return twMerge(clsx_default(inputs));
};
