// Jedno źródło prawdy dla wyglądu obu aplikacji.
//
// Dlaczego CommonJS, a nie TypeScript: tailwind.config.js jest ładowany przez
// Node bez transpilacji, więc pakiet w czystym TypeScripcie byłby stamtąd nie do
// odczytania bez kroku budowania — a ADR 0005 mówi, że pakiety konsumujemy jako
// źródło. Typy stoją obok, w index.d.ts, więc kod aplikacji nadal jest typowany.
//
// Ten plik zawiera wyłącznie dane. Przełożenie ich na konfigurację Tailwinda
// robi adapter po stronie aplikacji, bo mobile stoi na Tailwindzie v3, a web na
// v4 — patrz docs/adr/0002-tokeny-designu-jako-obiekt-typescript.md

/**
 * Paleta. Skala `brand` to metaliczny akcent biżuterii; `neutral` to spokojne
 * tła, które nie konkurują ze zdjęciami produktów.
 */
const colors = {
  brand: {
    50: "#FBF7EF",
    100: "#F4EAD5",
    200: "#E8D3A8",
    300: "#DABA78",
    400: "#CBA152",
    500: "#B8873A",
    600: "#9A6C2E",
    700: "#7A5326",
    800: "#5C3E20",
    900: "#3F2B18",
  },
  neutral: {
    0: "#FFFFFF",
    50: "#FAF9F7",
    100: "#F2F0EC",
    200: "#E4E1DB",
    300: "#CBC7BF",
    400: "#A5A099",
    500: "#7C7770",
    600: "#5B5751",
    700: "#403D39",
    800: "#2A2825",
    900: "#1A1917",
    950: "#0E0D0C",
  },
  success: { 100: "#E3F3E8", 500: "#2E7D4F", 700: "#1F5A38" },
  warning: { 100: "#FBF0DA", 500: "#B57C13", 700: "#82590C" },
  danger: { 100: "#F9E3E1", 500: "#B3352C", 700: "#83231C" },
  info: { 100: "#E2ECF6", 500: "#2C6395", 700: "#1D486E" },
};

/**
 * Kroje: szeryfowy w nagłówkach, bezszeryfowy w treści — typowe zestawienie dla
 * biżuterii. Nazwy rodzin muszą być zarejestrowane po stronie aplikacji
 * (expo-font na mobile, next/font na web); tutaj są tylko deklaracje.
 */
const fontFamily = {
  display: ["Playfair Display", "Georgia", "serif"],
  body: ["Inter", "system-ui", "sans-serif"],
  mono: ["ui-monospace", "SFMono-Regular", "monospace"],
};

/** Skala rozmiarów: [rozmiar, wysokość linii]. */
const fontSize = {
  xs: ["12px", "16px"],
  sm: ["14px", "20px"],
  base: ["16px", "24px"],
  lg: ["18px", "28px"],
  xl: ["20px", "28px"],
  "2xl": ["24px", "32px"],
  "3xl": ["30px", "38px"],
  "4xl": ["36px", "44px"],
  "5xl": ["48px", "56px"],
};

const fontWeight = {
  regular: "400",
  medium: "500",
  semibold: "600",
  bold: "700",
};

const borderRadius = {
  none: "0px",
  sm: "4px",
  md: "8px",
  lg: "12px",
  xl: "20px",
  full: "9999px",
};

/**
 * Cienie w zapisie CSS. NativeWind przekłada je na elevation na Androidzie i na
 * shadow* na iOS, więc wystarczy jeden zapis dla obu celów.
 */
const boxShadow = {
  sm: "0 1px 2px rgba(26, 25, 23, 0.06)",
  md: "0 4px 12px rgba(26, 25, 23, 0.08)",
  lg: "0 12px 32px rgba(26, 25, 23, 0.12)",
};

/** Progi responsywności — wspólne dla obu aplikacji. */
const screens = {
  sm: "640px",
  md: "768px",
  lg: "1024px",
  xl: "1280px",
  "2xl": "1536px",
};

/**
 * Dodatki do domyślnej skali odstępów Tailwinda. Świadomie nie zastępujemy jej
 * w całości — podmiana skali zerwałaby każdą klasę odstępu w obu aplikacjach
 * naraz, a zysk byłby żaden.
 */
const spacing = {
  4.5: "18px",
  13: "52px",
  18: "72px",
  22: "88px",
};

module.exports = {
  colors,
  fontFamily,
  fontSize,
  fontWeight,
  borderRadius,
  boxShadow,
  screens,
  spacing,
};
