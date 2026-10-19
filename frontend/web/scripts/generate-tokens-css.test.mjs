import { describe, expect, test } from "bun:test";

import tokens from "@olivin/tokens";

import { buildTokensCss } from "./generate-tokens-css.mjs";

/**
 * Adapter tokenów musi wystawić semantyczne nazwy shadcn, ale każda z nich
 * pochodzi z palety `@olivin/tokens` — komponent nie może nosić własnego
 * koloru. Test wiąże oba zbiory, więc zmiana palety automatycznie zmienia
 * motyw, a wpisanie literału w adapterze czerwieni ten test.
 */
describe("buildTokensCss", () => {
  test("maps shadcn semantic colors to design tokens", () => {
    const css = buildTokensCss(tokens);

    const expected = {
      background: tokens.colors.neutral[50],
      foreground: tokens.colors.neutral[900],
      card: tokens.colors.neutral[0],
      "card-foreground": tokens.colors.neutral[900],
      popover: tokens.colors.neutral[0],
      "popover-foreground": tokens.colors.neutral[900],
      primary: tokens.colors.brand[600],
      "primary-foreground": tokens.colors.neutral[0],
      secondary: tokens.colors.neutral[100],
      "secondary-foreground": tokens.colors.neutral[900],
      muted: tokens.colors.neutral[100],
      "muted-foreground": tokens.colors.neutral[600],
      accent: tokens.colors.brand[50],
      "accent-foreground": tokens.colors.brand[700],
      destructive: tokens.colors.danger[500],
      "destructive-foreground": tokens.colors.neutral[0],
      border: tokens.colors.neutral[200],
      input: tokens.colors.neutral[200],
      ring: tokens.colors.brand[500],
      "chart-1": tokens.colors.brand[500],
      "chart-2": tokens.colors.info[500],
      "chart-3": tokens.colors.success[500],
      "chart-4": tokens.colors.warning[500],
      "chart-5": tokens.colors.danger[500],
      sidebar: tokens.colors.neutral[0],
      "sidebar-foreground": tokens.colors.neutral[900],
      "sidebar-primary": tokens.colors.brand[600],
      "sidebar-primary-foreground": tokens.colors.neutral[0],
      "sidebar-accent": tokens.colors.neutral[100],
      "sidebar-accent-foreground": tokens.colors.neutral[900],
      "sidebar-border": tokens.colors.neutral[200],
      "sidebar-ring": tokens.colors.brand[500],
    };

    for (const [name, value] of Object.entries(expected)) {
      expect(css).toContain(`--color-${name}: ${value};`);
    }
  });

  test("resets the default Tailwind palette before the token colors", () => {
    const css = buildTokensCss(tokens);

    expect(css).toContain("@theme {\n  --color-*: initial;\n");
  });

  test("keeps the raw token scales available to Tailwind", () => {
    const css = buildTokensCss(tokens);

    expect(css).toContain(`--color-brand-600: ${tokens.colors.brand[600]};`);
    expect(css).toContain(`--radius-md: ${tokens.borderRadius.md};`);
  });
});
