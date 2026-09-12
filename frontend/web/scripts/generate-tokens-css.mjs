// Adapter tokenów dla Tailwinda v4.
//
// Mobile stoi na Tailwindzie v3, gdzie tokeny wstrzykuje się obiektem w
// tailwind.config.js. Web stoi na v4, gdzie motyw deklaruje się w CSS blokiem
// @theme. Wspólny preset między tymi wersjami nie istnieje — wspólne jest
// źródło danych, a każda aplikacja ma własny cienki adapter.
// Patrz docs/adr/0002-tokeny-designu-jako-obiekt-typescript.md
//
// Uruchamiane przez `bun run tokens`. Wynik jest commitowany, żeby budowanie nie
// zależało od kolejności kroków.

import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import tokens from "@olivin/tokens";

const here = dirname(fileURLToPath(import.meta.url));
const outputPath = join(here, "..", "app", "tokens.css");

const lines = [];

for (const [scale, shades] of Object.entries(tokens.colors)) {
  for (const [shade, value] of Object.entries(shades)) {
    lines.push(`  --color-${scale}-${shade}: ${value};`);
  }
}

for (const [name, stack] of Object.entries(tokens.fontFamily)) {
  lines.push(`  --font-${name}: ${stack.join(", ")};`);
}

for (const [name, [size, lineHeight]] of Object.entries(tokens.fontSize)) {
  lines.push(`  --text-${name}: ${size};`);
  lines.push(`  --text-${name}--line-height: ${lineHeight};`);
}

for (const [name, value] of Object.entries(tokens.fontWeight)) {
  lines.push(`  --font-weight-${name}: ${value};`);
}

for (const [name, value] of Object.entries(tokens.borderRadius)) {
  lines.push(`  --radius-${name}: ${value};`);
}

for (const [name, value] of Object.entries(tokens.boxShadow)) {
  lines.push(`  --shadow-${name}: ${value};`);
}

for (const [name, value] of Object.entries(tokens.screens)) {
  lines.push(`  --breakpoint-${name}: ${value};`);
}

for (const [name, value] of Object.entries(tokens.spacing)) {
  lines.push(`  --spacing-${name}: ${value};`);
}

const contents = [
  "/* Wygenerowane z @olivin/tokens przez scripts/generate-tokens-css.mjs.",
  "   Nie edytuj ręcznie — zmieniaj wartości w pakiecie tokenów. */",
  "@theme {",
  ...lines,
  "}",
  "",
].join("\n");

writeFileSync(outputPath, contents, "utf8");

console.log(`Zapisano ${lines.length} tokenów do ${outputPath}`);
