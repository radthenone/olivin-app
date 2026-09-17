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
    // eslint-config-expo 57 włącza reguły React Compilera. Synchronizacja
    // formularzy ze stanem serwera (setState w efekcie po zmianie danych
    // zapytania) jest u nas świadomym wzorcem — do przepisania osobnym
    // taskiem, nie przy okazji podbicia SDK. Do tego czasu ostrzeżenie.
    rules: {
      "react-hooks/set-state-in-effect": "warn",
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
