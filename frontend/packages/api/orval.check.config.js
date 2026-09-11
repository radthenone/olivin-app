// Konfiguracja wyłącznie do kontroli rozjazdu. Generuje klienta obok, do
// katalogu tymczasowego, żeby dało się go porównać z wersją zapisaną w
// repozytorium — dokładnie tym wzorcem, którym działają `db:migrations:check`
// i `backend:schema:check`: generujemy obok i porównujemy, zamiast ufać, że
// ktoś pamiętał o kroku ręcznym.
//
// Katalog kontrolny leży na tej samej głębokości co `generated/`, bo Orval
// wylicza ścieżki importu mutatorów względem pliku wynikowego. Inna głębokość
// dałaby inne ścieżki i kontrola zgłaszałaby różnicę, której nie ma.

const base = require("./orval.config.js");

const CHECK_DIR = "./.orval-check";

function rewrite(value) {
  return typeof value === "string"
    ? value.replace("./generated", CHECK_DIR)
    : value;
}

module.exports = Object.fromEntries(
  Object.entries(base).map(([name, config]) => [
    name,
    {
      ...config,
      output: {
        ...config.output,
        target: rewrite(config.output.target),
        ...(config.output.schemas
          ? { schemas: rewrite(config.output.schemas) }
          : {}),
      },
    },
  ]),
);
