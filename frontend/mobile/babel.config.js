module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      ["babel-preset-expo", { jsxImportSource: "nativewind" }],
      "nativewind/babel",
    ],
    plugins: [
      [
        "module-resolver",
        {
          root: ["./"],
          extensions: [".ts", ".tsx", ".js", ".jsx", ".json"],
          alias: {
            "@app": "./app",
            "@assets": "./assets",
            "@lib": "./lib",
            "@styles": "./styles",
            "@core": "./src/core",
            "@config": "./src/core/config",
            "@http": "./src/core/http",
            "@api": "./src/api",
            "@features": "./src/features",
            "@ui": "./src/ui",
          },
        },
      ],
      "react-native-reanimated/plugin",
    ],
  };
};
