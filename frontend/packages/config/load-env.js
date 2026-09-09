const { config } = require("dotenv");
const path = require("path");
const fs = require("fs");

// Pliki env leżą w korzeniu repo, a ten plik w głębi monorepo. Liczenie
// poziomów w górę ("../..") psuje się przy każdym przeniesieniu katalogu i robi
// to po cichu: brak zmiennej to nie błąd, tylko inny wynik. Dlatego szukamy
// korzenia po markerze, a nie po odległości.
const findRepoRoot = () => {
  let dir = __dirname;

  for (;;) {
    if (fs.existsSync(path.join(dir, "Taskfile.yml"))) {
      return dir;
    }

    const parent = path.dirname(dir);
    if (parent === dir) {
      return null;
    }

    dir = parent;
  }
};

const loadEnv = () => {
  const repoRoot = findRepoRoot();

  if (!repoRoot) {
    throw new Error(
      "Nie znaleziono korzenia repozytorium (szukano Taskfile.yml w górę od " +
        __dirname +
        "). Bez niego zmienne EXPO_PUBLIC_* nie zostaną wczytane.",
    );
  }

  const envPath = path.join(repoRoot, ".env");
  const expoEnvPath = path.join(repoRoot, ".envs", "dev", "expo.env");

  if (fs.existsSync(expoEnvPath)) {
    config({ path: expoEnvPath, override: true });
  }

  config({ path: envPath, override: true });
};

module.exports = { loadEnv };
