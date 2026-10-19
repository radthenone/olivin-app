import { describe, expect, test } from "bun:test";
import { ESLint } from "eslint";
import { join } from "node:path";

const root = join(import.meta.dir, "..");
const eslint = new ESLint({ cwd: root });

async function restrictedImports(code, filePath) {
  const [result] = await eslint.lintText(code, {
    filePath: join(root, filePath),
  });

  return result.messages.filter(
    (message) => message.ruleId === "no-restricted-imports",
  );
}

const uiFile = "src/components/ui/__fixture.tsx";
const featureFile = "src/features/auth/__fixture.tsx";

const forbidden = [
  "@olivin/api",
  "@olivin/api/generated/health",
  "@olivin/features",
  "@olivin/features/auth",
  "next-intl",
  "next-intl/server",
  "next/navigation",
  "next/navigation.js",
];

describe("ESLint boundaries for ui components", () => {
  for (const moduleName of forbidden) {
    test(`rejects ${moduleName} inside ui/`, async () => {
      const result = await restrictedImports(
        `import { thing } from "${moduleName}";\nexport const value = thing;`,
        uiFile,
      );

      expect(result.length).toBeGreaterThan(0);
    });
  }

  test("allows the same imports outside ui/", async () => {
    const result = await restrictedImports(
      'import { getTranslations } from "next-intl/server";\nexport const value = getTranslations;',
      featureFile,
    );

    expect(result).toEqual([]);
  });

  test("allows primitive and token imports inside ui/", async () => {
    const result = await restrictedImports(
      'import { Slot } from "@radix-ui/react-slot";\nimport { cn } from "@/lib/utils";\nexport const value = { Slot, cn };',
      uiFile,
    );

    expect(result).toEqual([]);
  });
});
