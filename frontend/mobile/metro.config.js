const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");

const config = getDefaultConfig(__dirname);

config.resolver.platforms = ["ios", "android", "native", "web"];

module.exports = withNativeWind(config, { input: "./styles/global.css" });
