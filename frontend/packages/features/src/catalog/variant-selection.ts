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
 * Wyciąga aktywne atrybuty produktu (te, które mają niepuste wartości w wariantach).
 *
 * Args:
 *     variants: Lista wariantów produktu.
 *
 * Returns:
 *     Lista definicji atrybutów wraz z unikalnymi wartościami występującymi w wariantach.
 */
export function getAttributeDefinitions(
  variants: readonly ProductVariant[],
): AttributeDefinition[] {
  const definitions: AttributeDefinition[] = [];

  for (const name of VARIANT_ATTRIBUTE_NAMES) {
    const valuesSet = new Set<string>();

    for (const v of variants) {
      const raw = v[name];
      const str = raw !== undefined && raw !== null ? String(raw).trim() : "";
      if (str.length > 0) {
        valuesSet.add(str);
      }
    }

    if (valuesSet.size > 0) {
      definitions.push({
        name,
        values: Array.from(valuesSet),
      });
    }
  }

  return definitions;
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

  return variants.find((v) => {
    return defs.every((def) => {
      const selectedVal = selection[def.name];
      if (!selectedVal) {
        return true;
      }
      return String(v[def.name] ?? "") === selectedVal;
    });
  });
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

  return variants.some((v) => {
    if (String(v[attribute] ?? "") !== value) {
      return false;
    }

    // Pozostałe aktywne atrybuty muszą się zgadzać z obecnym wyborem
    return defs.every((def) => {
      if (def.name === attribute) {
        return true;
      }
      const selectedVal = currentSelection[def.name];
      if (!selectedVal) {
        return true;
      }
      return String(v[def.name] ?? "") === selectedVal;
    });
  });
}

/**
 * Sprawdza, czy wariant pasujący do danej opcji jest dostępny w magazynie (`isAvailable`).
 *
 * Args:
 *     variants: Lista wariantów produktu.
 *     currentSelection: Aktualnie wybrane atrybuty.
 *     attribute: Nazwa sprawdzanego atrybutu.
 *     value: Sprawdzana wartość.
 *
 * Returns:
 *     `true`, jeśli pasujący wariant ma flagę `isAvailable: true`.
 */
export function isOptionAvailable(
  variants: readonly ProductVariant[],
  currentSelection: VariantSelection,
  attribute: VariantAttributeName,
  value: string,
): boolean {
  const targetSelection: VariantSelection = {
    ...currentSelection,
    [attribute]: value,
  };

  const matching = findMatchingVariant(variants, targetSelection);
  return matching ? matching.isAvailable : false;
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

  const selection: VariantSelection = {};
  if (!target) {
    return selection;
  }

  for (const name of VARIANT_ATTRIBUTE_NAMES) {
    const raw = target[name];
    const str = raw !== undefined && raw !== null ? String(raw).trim() : "";
    if (str.length > 0) {
      selection[name] = str;
    }
  }

  return selection;
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
      setSelectedAttributes((prev) => {
        const next: VariantSelection = { ...prev, [name]: value };

        // Jeśli nowa kombinacja nie istnieje bezpośrednio, spróbuj znaleźć
        // wariant zawierający tę wartość, dopasowując pozostałe atrybuty.
        if (!findMatchingVariant(variants, next)) {
          const alternative =
            variants.find(
              (v) => String(v[name] ?? "") === value && v.isAvailable,
            ) ?? variants.find((v) => String(v[name] ?? "") === value);

          if (alternative) {
            return getInitialSelection(variants, alternative.id);
          }
        }

        return next;
      });
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
