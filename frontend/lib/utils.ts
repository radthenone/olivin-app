import { Platform } from "react-native";
import { ps } from "./ps";
import { variants } from "./variants";
import { twMerge } from "tailwind-merge";
import clsx_default, { type ClassValue } from "clsx";

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

/**
 * Flaga określająca, czy aplikacja działa w środowisku przeglądarkowym.
 */
export const isWeb = Platform.OS === "web";

/**
 * Flaga określająca, czy aplikacja działa na systemie Android.
 */
export const isNative = Platform.OS === "android" || Platform.OS === "ios";

export {
  /** Funkcja pomocnicza do selekcji wartości zależnie od platformy. */
  ps,
  /** Definicje wariantów stylów dla komponentów. */
  variants,
};
