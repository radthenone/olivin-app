const { getDefaultConfig } = require("expo/metro-config");
const path = require("path");

// Absolute paths
const projectRoot = __dirname;
const monorepoRoot = path.resolve(projectRoot, "..");
const packagesDir = path.resolve(monorepoRoot, "packages");
const packLoggerFrontend = path.resolve(packagesDir, "pack-logger/frontend");

const config = getDefaultConfig(projectRoot);

// 1. watchFolders - Metro must watch changes in local packages
config.watchFolders = [
  projectRoot,
  monorepoRoot,
  packLoggerFrontend,
  // Watch both src and dist for hot reload
  path.resolve(packLoggerFrontend, "src"),
  path.resolve(packLoggerFrontend, "dist"),
];

// 2. Resolver - configure aliases and module resolution
config.resolver = {
  ...config.resolver,

  // Aliases for local packages
  extraNodeModules: {
    ...config.resolver.extraNodeModules,
    "@pack/logger": packLoggerFrontend,
  },

  // Paths to node_modules (hierarchy: frontend -> root)
  nodeModulesPaths: [
    path.resolve(projectRoot, "node_modules"),
    path.resolve(monorepoRoot, "node_modules"),
    path.resolve(packLoggerFrontend, "node_modules"),
  ],

  // Rozszerzenia plików - Metro obsługuje TypeScript natywnie
  sourceExts: [...config.resolver.sourceExts, "ts", "tsx", "mts", "cts"],

  // BlockList - ignoruj niepotrzebne katalogi (optymalizacja wydajności)
  blockList: [
    // block pack-logger/backend
    /packages\/pack-logger\/backend/,
    // block backend in root
    new RegExp(
      `${path.resolve(monorepoRoot, "backend").replace(/\\/g, "/")}/.*`
    ),
    // block git
    /\.git\/.*/,
    // block vscode
    /\.vscode\/.*/,
    // block expo
    /\.expo\/.*/,
    // block node_modules
    /node_modules\/.*/,
  ],

  // Enable package exports for local packages
  unstable_enablePackageExports: true,
};

// 3. Transformer - configure for TypeScript and other transformations
config.transformer = {
  ...config.transformer,
  // Enable inline requires for better performance
  inlineRequires: true,
};

module.exports = config;
