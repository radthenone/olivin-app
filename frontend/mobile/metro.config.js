const path = require("path");
const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");

const config = getDefaultConfig(__dirname);

config.resolver.platforms = ["ios", "android", "native", "web"];

// W monorepo korzeniem serwera Metro jest frontend/, więc obserwator plików
// skanuje także katalogi wynikowe innych workspace'ów: build Next.js, pełny
// build natywny Androida po kompilacji C++, katalog kontroli Orvala. Na Windowsie
// przekracza to limit czasu startu obserwatora ("Failed to start watch mode") i
// Metro pada, zanim cokolwiek zbuduje. Te katalogi nigdy nie są źródłem modułów.
const workspaceRoot = path.resolve(__dirname, "..");
const escape = (p) => p.replace(/[\\/]/g, "[\\\\/]");
const excluded = [
  "web/.next",
  "web/out",
  "mobile/android/build",
  "mobile/android/app/build",
  "mobile/android/app/.cxx",
  "mobile/android/.gradle",
  "packages/api/.orval-check",
  ".turbo",
].map(
  (dir) => new RegExp(`^${escape(path.join(workspaceRoot, dir))}[\\\\/].*`),
);

config.resolver.blockList = [
  ...(Array.isArray(config.resolver.blockList)
    ? config.resolver.blockList
    : config.resolver.blockList
      ? [config.resolver.blockList]
      : []),
  ...excluded,
];

module.exports = withNativeWind(config, { input: "./styles/global.css" });
