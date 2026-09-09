const { config } = require("dotenv");
const path = require("path");
const fs = require("fs");

const loadEnv = () => {
  const envPath = path.resolve(__dirname, "../.env");
  const expoEnvPath = path.resolve(__dirname, "../.envs/dev/expo.env");

  if (fs.existsSync(expoEnvPath)) {
    config({ path: expoEnvPath, override: true });
  }

  config({ path: envPath, override: true });
};

module.exports = { loadEnv };
