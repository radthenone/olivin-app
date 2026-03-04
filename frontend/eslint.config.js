// https://docs.expo.dev/guides/using-eslint/
const { defineConfig } = require("eslint/config");
const expoConfig = require("eslint-config-expo/flat.js");

module.exports = defineConfig([
  expoConfig,
  {
    ignores: [
      "dist/*",
      "build/*",
      "node_modules/*",
      "**/*.d.ts",
      "metro.config.js",
      "babel.config.js",
      "app.config.js",
    ],
  },
  {
    settings: {
      "import/resolver": {
        typescript: {
          alwaysTryTypes: true,
          project: "./tsconfig.json",
        },
      },
    },
  },
]);
