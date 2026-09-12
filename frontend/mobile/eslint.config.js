const { defineConfig } = require("eslint/config");
const expoConfig = require("eslint-config-expo/flat.js");
const path = require("path");

const {
  sharedIgnores,
  platformExtensions,
} = require("@olivin/config/eslint/base.js");

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
          extensions: platformExtensions,
        },
      },
    },
  },
  {
    ignores: [
      ...sharedIgnores,
      // Pliki konfiguracyjne aplikacji Expo — CommonJS, poza grafem aplikacji.
      "metro.config.js",
      "babel.config.js",
      "app.config.js",
      "orval.config.js",
      "eslint.config.js",
      "load-env.js",
    ],
  },
]);
