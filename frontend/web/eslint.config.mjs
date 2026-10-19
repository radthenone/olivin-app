import { defineConfig } from "eslint/config";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

import olivin from "@olivin/config/eslint/base.js";

export default defineConfig([
  ...nextCoreWebVitals,
  ...nextTypescript,
  {
    ignores: [...olivin.sharedIgnores, ".next/**", "next-env.d.ts"],
  },
  {
    // Komponenty ui/ są czyste: dane, nawigacja i i18n należą do warstwy
    // wyżej. Reguła obejmuje też podścieżki, bo import z `@olivin/api/generated`
    // jest tym samym naruszeniem co import z pakietu głównego.
    files: ["src/components/ui/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          paths: [
            {
              name: "@olivin/api",
              message:
                "Komponenty ui/ nie pobierają danych — dane wstrzykuje warstwa wyżej.",
            },
            {
              name: "@olivin/features",
              message:
                "Komponenty ui/ nie zależą od features — kierunek zależności jest odwrotny.",
            },
            {
              name: "next-intl",
              message:
                "Komponenty ui/ dostają teksty przez propsy, nie przez i18n.",
            },
            {
              name: "next/navigation",
              message:
                "Komponenty ui/ nie nawigują — nawigację robi warstwa wyżej.",
            },
          ],
          patterns: [
            {
              group: [
                "@olivin/api/*",
                "@olivin/features/*",
                "next-intl/*",
                "next/navigation/*",
                "next/navigation.js",
              ],
              message:
                "Komponenty ui/ są czyste: bez danych, nawigacji i i18n.",
            },
          ],
        },
      ],
    },
  },
]);
