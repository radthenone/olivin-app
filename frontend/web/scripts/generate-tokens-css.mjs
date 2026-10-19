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
import { fileURLToPath, pathToFileURL } from "node:url";

import tokens from "@olivin/tokens";

const here = dirname(fileURLToPath(import.meta.url));
const outputPath = join(here, "..", "app", "tokens.css");

/**
 * Semantyczne role shadcn/ui. Każda wskazuje na wpis z palety `@olivin/tokens`
 * — komponenty `ui/` nie znają nazw surowych skal, więc zmiana palety wystarcza,
 * żeby zmienić cały motyw.
 */
function semanticColors(palette) {
  return {
    background: palette.colors.neutral[50],
    foreground: palette.colors.neutral[900],
    card: palette.colors.neutral[0],
    "card-foreground": palette.colors.neutral[900],
    popover: palette.colors.neutral[0],
    "popover-foreground": palette.colors.neutral[900],
    primary: palette.colors.brand[600],
    "primary-foreground": palette.colors.neutral[0],
    secondary: palette.colors.neutral[100],
    "secondary-foreground": palette.colors.neutral[900],
    muted: palette.colors.neutral[100],
    "muted-foreground": palette.colors.neutral[600],
    accent: palette.colors.brand[50],
    "accent-foreground": palette.colors.brand[700],
    destructive: palette.colors.danger[500],
    "destructive-foreground": palette.colors.neutral[0],
    border: palette.colors.neutral[200],
    input: palette.colors.neutral[200],
    ring: palette.colors.brand[500],
    "chart-1": palette.colors.brand[500],
    "chart-2": palette.colors.info[500],
    "chart-3": palette.colors.success[500],
    "chart-4": palette.colors.warning[500],
    "chart-5": palette.colors.danger[500],
    sidebar: palette.colors.neutral[0],
    "sidebar-foreground": palette.colors.neutral[900],
    "sidebar-primary": palette.colors.brand[600],
    "sidebar-primary-foreground": palette.colors.neutral[0],
    "sidebar-accent": palette.colors.neutral[100],
    "sidebar-accent-foreground": palette.colors.neutral[900],
    "sidebar-border": palette.colors.neutral[200],
    "sidebar-ring": palette.colors.brand[500],
  };
}

/** Buduje zawartość `app/tokens.css`. Czysta funkcja — testowana bez zapisu. */
export function buildTokensCss(palette) {
  const lines = [];

  for (const [scale, shades] of Object.entries(palette.colors)) {
    for (const [shade, value] of Object.entries(shades)) {
      lines.push(`  --color-${scale}-${shade}: ${value};`);
    }
  }

  for (const [name, value] of Object.entries(semanticColors(palette))) {
    if (!value) {
      throw new Error(`Brak tokenu koloru dla roli "${name}".`);
    }
    lines.push(`  --color-${name}: ${value};`);
  }

  for (const [name, stack] of Object.entries(palette.fontFamily)) {
    lines.push(`  --font-${name}: ${stack.join(", ")};`);
  }

  for (const [name, [size, lineHeight]] of Object.entries(palette.fontSize)) {
    lines.push(`  --text-${name}: ${size};`);
    lines.push(`  --text-${name}--line-height: ${lineHeight};`);
  }

  for (const [name, value] of Object.entries(palette.fontWeight)) {
    lines.push(`  --font-weight-${name}: ${value};`);
  }

  for (const [name, value] of Object.entries(palette.borderRadius)) {
    lines.push(`  --radius-${name}: ${value};`);
  }

  for (const [name, value] of Object.entries(palette.boxShadow)) {
    lines.push(`  --shadow-${name}: ${value};`);
  }

  for (const [name, value] of Object.entries(palette.screens)) {
    lines.push(`  --breakpoint-${name}: ${value};`);
  }

  for (const [name, value] of Object.entries(palette.spacing)) {
    lines.push(`  --spacing-${name}: ${value};`);
  }

  return [
    "/* Wygenerowane z @olivin/tokens przez scripts/generate-tokens-css.mjs.",
    "   Nie edytuj ręcznie — zmieniaj wartości w pakiecie tokenów. */",
    "@theme {",
    ...lines,
    "}",
    "",
  ].join("\n");
}

const isMain =
  process.argv[1] !== undefined &&
  import.meta.url === pathToFileURL(process.argv[1]).href;

if (isMain) {
  const contents = buildTokensCss(tokens);
  writeFileSync(outputPath, contents, "utf8");
  const count = contents.split("\n").filter((line) => line.includes(":")).length;
  console.log(`Zapisano ${count} tokenów do ${outputPath}`);
}
