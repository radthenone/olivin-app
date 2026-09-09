const nativewind = require("nativewind/preset");
const tokens = require("@olivin/tokens");

// Adapter tokenów dla Tailwinda v3 (wymaganego przez NativeWind 4).
// Web ma własny adapter dla v4 — patrz docs/adr/0002-tokeny-designu-jako-obiekt-typescript.md
// Wartości nie powstają tutaj; ten plik wyłącznie przekłada pakiet tokenów na
// kształt konfiguracji, którego oczekuje Tailwind.

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./styles/global.css",
    "./app/**/*.{js,jsx,ts,tsx}",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  presets: [nativewind],
  theme: {
    screens: tokens.screens,
    extend: {
      colors: tokens.colors,
      fontFamily: tokens.fontFamily,
      fontSize: tokens.fontSize,
      fontWeight: tokens.fontWeight,
      borderRadius: tokens.borderRadius,
      boxShadow: tokens.boxShadow,
      spacing: tokens.spacing,
    },
  },
  plugins: [],
};
