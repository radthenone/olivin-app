const { defineConfig } = require("eslint/config");
const expoConfig = require("eslint-config-expo/flat.js");
const path = require("path");

module.exports = defineConfig([
  expoConfig,
  {
    settings: {
      "import/resolver": {
        typescript: {
          alwaysTryTypes: true,
          project: path.resolve(__dirname, "./tsconfig.json"),
        },
        node: {
          extensions: [
            ".android.cjs",
            ".android.mjs",
            ".android.js",
            ".android.jsx",
            ".android.ts",
            ".android.tsx",
            ".ios.cjs",
            ".ios.mjs",
            ".ios.js",
            ".ios.jsx",
            ".ios.ts",
            ".ios.tsx",
            ".native.cjs",
            ".native.mjs",
            ".native.js",
            ".native.jsx",
            ".native.ts",
            ".native.tsx",
            ".cjs",
            ".mjs",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".d.ts",
          ],
        },
      },
    },
  },
  {
    ignores: [
      "dist/*",
      "build/*",
      "node_modules/*",
      "**/*.d.ts",
      "metro.config.js",
      "babel.config.js",
      "app.config.js",
      "orval.config.js",
      "eslint.config.js",
      "load-env.js",
    ],
  },
]);
