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
]);
