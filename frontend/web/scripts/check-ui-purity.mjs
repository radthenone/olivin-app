// Strażnik czystości komponentów `src/components/ui/`.
//
// Komponenty shadcn są czyste: biorą style wyłącznie z tokenów. Ten skrypt
// odrzuca hexy oraz arbitralne wartości Tailwinda z liczbą albo kolorem
// (`w-[13px]`, `bg-[#fff]`, `text-[oklch(...)]`), a przepuszcza warianty
// stanu, które shadcn generuje (`data-[state=open]:`, `aria-[invalid=true]:`)
// i arbitralne selektory (`[&>svg]:`).
//
// Uruchamiany w `bun run lint` oraz jako osobny krok CI.

import { readdirSync, readFileSync } from "node:fs";
import { dirname, extname, join, relative } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const uiDir = join(here, "..", "src", "components", "ui");

const HEX = /#(?:[0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{4}|[0-9a-f]{3})\b/gi;
const COLOR_FUNCTION = /\b(?:rgba?|hsla?|oklch|oklab|lab|lch|color)\s*\(/i;
const BRACKET = /\[[^\]\n]*\]/g;
const VARIANT_PREFIX =
  /(?:^|[\s"'`])(?:(?:group|peer)-)?(?:data|aria|has|not|in|supports|nth(?:-[a-z-]+)?)-$/;
const SELECTOR_START = /^[&:>+~*.]/;

function isVariantSelector(content, prefix) {
  return SELECTOR_START.test(content.trim()) || VARIANT_PREFIX.test(prefix);
}

/**
 * Sprawdza pojedynczy plik. Zwraca listę naruszeń z numerem linii, żeby CI
 * wskazywało miejsce, a nie tylko fakt.
 */
export function checkSource(source, file) {
  const violations = [];

  source.split(/\r?\n/).forEach((line, index) => {
    const report = (match, reason) =>
      violations.push({
        file,
        line: index + 1,
        column: match.index + 1,
        text: line.trim(),
        reason,
      });

    for (const match of line.matchAll(HEX)) {
      report(match, "hex color");
    }

    for (const match of line.matchAll(BRACKET)) {
      const content = match[0].slice(1, -1);
      const prefix = line.slice(Math.max(0, match.index - 40), match.index);

      // Hex w wartości zgłasza już pętla wyżej — nie duplikujemy komunikatu.
      if (isVariantSelector(content, prefix) || content.match(HEX)) {
        continue;
      }

      if (COLOR_FUNCTION.test(content)) {
        report(match, "arbitrary color value");
      } else if (/\d/.test(content)) {
        report(match, "arbitrary numeric value");
      }
    }
  });

  return violations;
}

function collectFiles(directory) {
  const files = [];

  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);

    if (entry.isDirectory()) {
      files.push(...collectFiles(path));
      continue;
    }

    if ([".ts", ".tsx"].includes(extname(entry.name))) {
      files.push(path);
    }
  }

  return files;
}

const isMain =
  process.argv[1] !== undefined &&
  import.meta.url === pathToFileURL(process.argv[1]).href;

if (isMain) {
  let files = [];

  try {
    files = collectFiles(uiDir);
  } catch (error) {
    if (error.code !== "ENOENT") {
      throw error;
    }
  }

  const violations = files.flatMap((file) =>
    checkSource(readFileSync(file, "utf8"), relative(process.cwd(), file)),
  );

  if (violations.length > 0) {
    for (const violation of violations) {
      console.error(
        `${violation.file}:${violation.line}:${violation.column} ${violation.reason} — ${violation.text}`,
      );
    }
    console.error(
      `\nKomponenty ui/ mają brać style wyłącznie z tokenów (${violations.length} naruszeń).`,
    );
    process.exitCode = 1;
  } else {
    console.log(`UI purity OK (${files.length} plików).`);
  }
}
