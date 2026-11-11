import { useCallback, useMemo, useState } from "react";
import type { ProductVariant } from "@olivin/api/generated/apps/schemas";

/**
 * Atrybuty wariantu, z których klient wybiera pożądaną konfigurację na karcie.
 */
export const VARIANT_ATTRIBUTE_NAMES = [
  "metalColor",
  "size",
  "length",
  "stone",
] as const;

export type VariantAttributeName = (typeof VARIANT_ATTRIBUTE_NAMES)[number];

export type VariantSelection = Partial<Record<VariantAttributeName, string>>;

export interface AttributeDefinition {
  name: VariantAttributeName;
  values: string[];
}

/**
 * Wartość atrybutu wariantu po normalizacji (`trim`). Brak wartości to `""` —
 * traktujemy go jak zwykłą wartość („bez kamienia”), a nie wildcard.
 */
function attrValue(
  variant: ProductVariant,
  name: VariantAttributeName,
): string {
  return String(variant[name] ?? "").trim();
}

/**
 * Wyciąga aktywne atrybuty produktu (te, które mają niepuste wartości w wariantach).
 *
 * Args:
 *     variants: Lista wariantów produktu.
 *
 * Returns:
 *     Lista definicji atrybutów wraz z unikalnymi wartościami występującymi w wariantach.
 *     Gdy atrybut ma tylko część wariantów, ostatnią wartością jest `""` („brak”).
 */
export function getAttributeDefinitions(
  variants: readonly ProductVariant[],
): AttributeDefinition[] {
  const definitions: AttributeDefinition[] = [];

  for (const name of VARIANT_ATTRIBUTE_NAMES) {
    const values = new Set<string>();
    let hasMissing = false;

    for (const v of variants) {
      const value = attrValue(v, name);
      if (value.length > 0) {
        values.add(value);
      } else {
        hasMissing = true;
      }
    }

    if (values.size > 0) {
      definitions.push({
        name,
        values: hasMissing ? [...values, ""] : [...values],
      });
    }
  }

  return definitions;
}

/**
 * Czy wariant zgadza się z wyborem na aktywnych atrybutach (poza `skip`).
 * Atrybut, którego wybór nie jest ustawiony (`undefined`), nie ogranicza dopasowania;
 * `""` ogranicza do wariantów bez tego atrybutu.
 */
function matchesSelection(
  variant: ProductVariant,
  defs: readonly AttributeDefinition[],
  selection: VariantSelection,
  skip?: VariantAttributeName,
): boolean {
  return defs.every((def) => {
    const selected = selection[def.name];
    return (
      def.name === skip ||
      selected === undefined ||
      attrValue(variant, def.name) === selected
    );
  });
}

/** Wybór atrybutów odpowiadający wariantowi (z `""` dla brakujących atrybutów). */
function selectionOf(
  variant: ProductVariant,
  defs: readonly AttributeDefinition[],
): VariantSelection {
  const selection: VariantSelection = {};
  for (const def of defs) {
    selection[def.name] = attrValue(variant, def.name);
  }
  return selection;
}

/**
 * Znajduje wariant, który pasuje do wybranej konfiguracji atrybutów.
 *
 * Args:
 *     variants: Lista wariantów produktu.
 *     selection: Wybrane wartości atrybutów.
 *
 * Returns:
 *     Pasujący wariant lub `undefined`, jeśli taka kombinacja nie istnieje.
 */
export function findMatchingVariant(
  variants: readonly ProductVariant[],
  selection: VariantSelection,
): ProductVariant | undefined {
  const defs = getAttributeDefinitions(variants);

  return variants.find((v) => matchesSelection(v, defs, selection));
}

/**
 * Sprawdza, czy dla danej opcji atrybutu istnieje jakakolwiek kombinacja
 * zgodna z pozostałymi wybranymi atrybutami.
 *
 * Args:
 *     variants: Lista wariantów produktu.
 *     currentSelection: Aktualnie wybrane atrybuty.
 *     attribute: Nazwa sprawdzanego atrybutu.
 *     value: Sprawdzana wartość.
 *
 * Returns:
 *     `true`, jeśli wariant łączący tę wartość z pozostałymi atrybutami istnieje w katalogu.
 */
export function isCombinationPossible(
  variants: readonly ProductVariant[],
  currentSelection: VariantSelection,
  attribute: VariantAttributeName,
  value: string,
): boolean {
  const defs = getAttributeDefinitions(variants);

  return variants.some(
    (v) =>
      attrValue(v, attribute) === value &&
      matchesSelection(v, defs, currentSelection, attribute),
  );
}

/**
 * Wybór po kliknięciu opcji: bieżący wybór z podmienioną wartością albo, gdy takiej
 * kombinacji nie ma, wybór najbliższego istniejącego wariantu z tą wartością.
 *
 * Najbliższy to ten, który zachowuje jak najwięcej wybranych atrybutów; przy remisie
 * wygrywa wariant dostępny w magazynie, potem pierwszy w kolejności.
 *
 * Args:
 *     variants: Lista wariantów produktu.
 *     currentSelection: Aktualnie wybrane atrybuty.
 *     attribute: Nazwa zmienianego atrybutu.
 *     value: Wybierana wartość.
 *
 * Returns:
 *     Nowy wybór albo `undefined`, gdy żaden wariant nie ma tej wartości.
 */
export function resolveSelection(
  variants: readonly ProductVariant[],
  currentSelection: VariantSelection,
  attribute: VariantAttributeName,
  value: string,
): VariantSelection | undefined {
  const next: VariantSelection = { ...currentSelection, [attribute]: value };
  if (findMatchingVariant(variants, next)) {
    return next;
  }

  const defs = getAttributeDefinitions(variants);
  let best: ProductVariant | undefined;
  let bestScore = -1;

  for (const v of variants) {
    if (attrValue(v, attribute) !== value) {
      continue;
    }

    const score = defs.filter(
      (def) =>
        def.name !== attribute &&
        attrValue(v, def.name) === currentSelection[def.name],
    ).length;

    if (
      score > bestScore ||
      (score === bestScore && v.isAvailable && !best?.isAvailable)
    ) {
      best = v;
      bestScore = score;
    }
  }

  return best ? selectionOf(best, defs) : undefined;
}

/**
 * Sprawdza, czy wariant wybrany po kliknięciu danej opcji jest dostępny w magazynie
 * (`isAvailable`). Gdy kombinacji z resztą wyboru nie ma, liczy się wariant, do którego
 * kliknięcie przeskoczy (patrz `resolveSelection`).
 *
 * Args:
 *     variants: Lista wariantów produktu.
 *     currentSelection: Aktualnie wybrane atrybuty.
 *     attribute: Nazwa sprawdzanego atrybutu.
 *     value: Sprawdzana wartość.
 *
 * Returns:
 *     `true`, jeśli ten wariant ma flagę `isAvailable: true`.
 */
export function isOptionAvailable(
  variants: readonly ProductVariant[],
  currentSelection: VariantSelection,
  attribute: VariantAttributeName,
  value: string,
): boolean {
  const resolved = resolveSelection(
    variants,
    currentSelection,
    attribute,
    value,
  );

  return (
    (resolved && findMatchingVariant(variants, resolved)?.isAvailable) ?? false
  );
}

/**
 * Ustala początkowy wybór atrybutów na karcie produktu.
 *
 * Args:
 *     variants: Lista wariantów.
 *     preferredVariantId: Opcjonalne ID preferowanego wariantu.
 *
 * Returns:
 *     Wybór atrybutów pierwszego dostępnego lub preferowanego wariantu.
 */
export function getInitialSelection(
  variants: readonly ProductVariant[],
  preferredVariantId?: string,
): VariantSelection {
  let target = preferredVariantId
    ? variants.find(
        (v) => v.id === preferredVariantId || v.sku === preferredVariantId,
      )
    : undefined;

  if (!target) {
    target = variants.find((v) => v.isAvailable) ?? variants[0];
  }

  return target ? selectionOf(target, getAttributeDefinitions(variants)) : {};
}

/**
 * Hook do zarządzania stanem wyboru wariantu na karcie produktu.
 *
 * Args:
 *     variants: Lista wariantów produktu.
 *     initialVariantId: Opcjonalne początkowe ID wariantu.
 *
 * Returns:
 *     Stan wyboru, pasujący wariant, definicje atrybutów i metody przełączania.
 */
export function useVariantSelection({
  variants,
  initialVariantId,
}: {
  variants: readonly ProductVariant[];
  initialVariantId?: string;
}) {
  const [selectedAttributes, setSelectedAttributes] =
    useState<VariantSelection>(() =>
      getInitialSelection(variants, initialVariantId),
    );

  const attributeDefinitions = useMemo(
    () => getAttributeDefinitions(variants),
    [variants],
  );

  const selectedVariant = useMemo(
    () => findMatchingVariant(variants, selectedAttributes),
    [variants, selectedAttributes],
  );

  const selectAttribute = useCallback(
    (name: VariantAttributeName, value: string) => {
      setSelectedAttributes(
        (prev) => resolveSelection(variants, prev, name, value) ?? prev,
      );
    },
    [variants],
  );

  const isPossible = useCallback(
    (name: VariantAttributeName, value: string) => {
      return isCombinationPossible(variants, selectedAttributes, name, value);
    },
    [variants, selectedAttributes],
  );

  const isAvailable = useCallback(
    (name: VariantAttributeName, value: string) => {
      return isOptionAvailable(variants, selectedAttributes, name, value);
    },
    [variants, selectedAttributes],
  );

  return {
    selectedAttributes,
    selectedVariant,
    attributeDefinitions,
    selectAttribute,
    isPossible,
    isAvailable,
  };
}
