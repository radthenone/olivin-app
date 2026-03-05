const { loadEnv } = require("./load-env");

loadEnv();

const ALLAUTH_TAGS = [
  "Configuration",
  "Authentication Account",
  "Authentication Password Reset",
  "Authentication Providers",
  "Authentication 2FA",
  "Authentication Login By Code",
  "Authentication Current Session",
  "Account Providers",
  "Account Email",
  "Account Phone",
  "Account 2FA",
  "Account Password",
  "Tokens",
];

const APPS_TAGS = ["Addresses", "Profiles", "Health"];

const ZOD_OVERRIDE = {
  zod: {
    generate: {
      body: true,
      param: true,
      query: true,
      response: true,
    },
    coerce: {
      param: true,
      query: true,
    },
  },
};

const ALLAUTH_SCHEMA_URL = `http://${process.env.EXPO_PUBLIC_BACKEND_URL || "localhost:8020"}/_allauth/openapi.json`;
const APPS_SCHEMA_URL = `http://${process.env.EXPO_PUBLIC_BACKEND_URL || "localhost:8020"}/api/schema/`;

module.exports = {
  "allauth-headless": {
    input: {
      target: ALLAUTH_SCHEMA_URL,
    },
    output: {
      mode: "tags-split",
      target: "./src/api/generated/auth",
      schemas: "./src/api/generated/auth/schemas",
      client: "react-query",
      httpClient: "axios",
      mock: false,
      override: {
        mutator: {
          path: "./src/api/auth-mutator.ts",
          name: "authInstance",
        },
      },
    },
  },

  "allauth-headless-zod": {
    input: {
      target: ALLAUTH_SCHEMA_URL,
    },
    output: {
      mode: "tags-split",
      target: "./src/api/generated/auth",
      fileExtension: ".zod.ts",
      client: "zod",
      httpClient: "axios",
      mock: false,
      override: ZOD_OVERRIDE,
    },
  },

  app: {
    input: {
      target: APPS_SCHEMA_URL,
      filters: { tags: APPS_TAGS },
    },
    output: {
      mode: "tags-split",
      target: "./src/api/generated/apps",
      schemas: "./src/api/generated/apps/schemas",
      client: "react-query",
      httpClient: "axios",
      mock: false,
      override: {
        mutator: {
          path: "./src/api/app-mutator.ts",
          name: "appInstance",
        },
      },
    },
  },

  "app-zod": {
    input: {
      target: APPS_SCHEMA_URL,
      filters: { tags: APPS_TAGS },
    },
    output: {
      mode: "tags-split",
      target: "./src/api/generated/apps",
      fileExtension: ".zod.ts",
      client: "zod",
      httpClient: "axios",
      mock: false,
      override: ZOD_OVERRIDE,
    },
  },
};
