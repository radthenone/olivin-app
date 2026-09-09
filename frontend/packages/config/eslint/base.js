// Reguły wspólne dla każdego workspace'a frontendu. Wszystko, co zależy od
// platformy (presety Expo, presety Next), zostaje w konfiguracji aplikacji —
// tutaj trafia tylko to, co jest prawdziwie wspólne.

/** Katalogi, których nie lintuje żaden workspace. */
const sharedIgnores = [
  "dist/*",
  "build/*",
  "node_modules/*",
  "**/*.d.ts",
  // Klient API generuje Orval. Formatuje i tak generator, a poprawki znikają
  // przy następnej regeneracji — ten sam katalog jest wykluczony w Prettierze
  // i w hookach pre-commit; trzymaj wszystkie trzy wpisy zgodne.
  "src/api/generated/**",
];

/** Rozszerzenia platformowe rozpoznawane przez resolver importów. */
const platformExtensions = [
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
  ".web.cjs",
  ".web.mjs",
  ".web.js",
  ".web.jsx",
  ".web.ts",
  ".web.tsx",
  ".cjs",
  ".mjs",
  ".js",
  ".jsx",
  ".ts",
  ".tsx",
  ".d.ts",
];

module.exports = { sharedIgnores, platformExtensions };
