import { cva } from "class-variance-authority";

/**
 * Definicje wariantów stylów dla komponentów.
 * Umożliwia łatwe zarządzanie różnymi wariantami stylów w aplikacji.
 */
export const variants = cva({
  padding: {
    xs: "0.25rem",
    sm: "0.5rem",
    md: "1rem",
    lg: "1.5rem",
    xl: "2rem",
  },
});
