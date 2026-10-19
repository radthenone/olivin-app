import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Łączy klasy warunkowe i rozwiązuje konflikty utility Tailwinda. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
