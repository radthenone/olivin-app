const path = require("path");

const { loadEnv } = require("@olivin/config/load-env.js");

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

const APPS_TAGS = [
  "Addresses",
  "Categories",
  "Collections",
  "Consents",
  "Products",
  "Profiles",
  "Health",
];

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

// Schematy czytamy z plikow w repozytorium, nie po HTTP. Powod jest praktyczny:
// bramka rozjazdu (task ovral:check) ma dzialac takze w ciaglej integracji, gdzie
// nie ma uruchomionego Django. Aktualnosc pliku schematu domenowego pilnuje
// osobna kontrola (task backend:schema:check), wiec lancuch jest zamkniety:
// kod Django -> schema.yaml -> wygenerowany klient.
//
// Snapshot schematu allauth odswieza `task ovral:schema:allauth` przy podbiciu
// wersji biblioteki — ten schemat pochodzi z zewnatrz i zmienia sie wylacznie
// razem z nia.
const REPO_ROOT = path.resolve(__dirname, "../../..");
const ALLAUTH_SCHEMA_URL = path.join(
  REPO_ROOT,
  "backend/src/allauth-schema.json",
);
const APPS_SCHEMA_URL = path.join(REPO_ROOT, "backend/src/schema.yaml");

module.exports = {
  "allauth-headless": {
    input: {
      target: ALLAUTH_SCHEMA_URL,
    },
    output: {
      mode: "tags-split",
      target: "./generated/auth",
      schemas: "./generated/auth/schemas",
      client: "react-query",
      httpClient: "fetch",
      mock: false,
      override: {
        mutator: {
          path: "./src/auth-mutator.ts",
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
      target: "./generated/auth",
      fileExtension: ".zod.ts",
      client: "zod",
      httpClient: "fetch",
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
      target: "./generated/apps",
      schemas: "./generated/apps/schemas",
      client: "react-query",
      httpClient: "fetch",
      mock: false,
      override: {
        mutator: {
          path: "./src/app-mutator.ts",
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
      target: "./generated/apps",
      fileExtension: ".zod.ts",
      client: "zod",
      httpClient: "fetch",
      mock: false,
      override: ZOD_OVERRIDE,
    },
  },
};
