"use client";

import type { ProductVariant } from "@olivin/api/generated/apps/schemas";
import {
  getAttributeDefinitions,
  isCombinationPossible,
  isOptionAvailable,
  type VariantAttributeName,
  type VariantSelection,
} from "@olivin/features/catalog";
import { messages, type Locale } from "@olivin/i18n";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * Zwraca czytelną etykietę dla wartości danego atrybutu w zadanym języku.
 */
function getOptionLabel(
  name: VariantAttributeName,
  value: string,
  locale: Locale,
): string {
  const catalog = messages[locale].catalog;

  if (name === "metalColor") {
    const key = value as keyof typeof catalog.metalColor;
    return catalog.metalColor[key] ?? value;
  }

  if (name === "stone") {
    const key = value as keyof typeof catalog.stone;
    return catalog.stone[key] ?? value;
  }

  if (name === "length") {
    return `${value} cm`;
  }

  return value;
}

/**
 * Przełącznik wariantów dostępny z klawiatury i czytnika ekranu.
 *
 * Renderuje grupy atrybutów jako semantyczne grupy opcji z klawiszami Tab/Enter/Space.
 * Niedostępne kombinacje (których nie ma w katalogu) są wyłączone (`disabled`),
 * a warianty wyprzedane są odpowiednio oznaczone.
 */
export function VariantSelector({
  variants,
  selectedAttributes,
  onSelect,
  locale,
}: {
  variants: readonly ProductVariant[];
  selectedAttributes: VariantSelection;
  onSelect?: (name: VariantAttributeName, value: string) => void;
  locale: Locale;
}) {
  const definitions = getAttributeDefinitions(variants);
  const catalog = messages[locale].catalog;

  if (definitions.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-5">
      {definitions.map((def) => {
        const groupLabel = catalog.product.attributes[def.name] ?? def.name;
        const currentVal = selectedAttributes[def.name];

        return (
          <fieldset
            aria-label={groupLabel}
            className="flex flex-col gap-2 border-none p-0"
            key={def.name}
            role="radiogroup"
          >
            <legend className="text-sm font-medium text-neutral-800">
              {groupLabel}
            </legend>
            <div className="flex flex-wrap gap-2">
              {def.values.map((val) => {
                const isSelected = currentVal === val;
                const isPossible = isCombinationPossible(
                  variants,
                  selectedAttributes,
                  def.name,
                  val,
                );
                const isAvailable = isOptionAvailable(
                  variants,
                  selectedAttributes,
                  def.name,
                  val,
                );

                const optionLabel = getOptionLabel(def.name, val, locale);

                let ariaLabel = optionLabel;
                if (!isPossible) {
                  ariaLabel = `${optionLabel} (${catalog.product.combinationUnavailable})`;
                } else if (!isAvailable) {
                  ariaLabel = `${optionLabel} (${catalog.product.availability.unavailable})`;
                }

                return (
                  <Button
                    aria-checked={isSelected}
                    aria-disabled={!isPossible}
                    aria-label={ariaLabel}
                    className={cn(
                      "relative h-9 px-3.5 text-xs font-medium transition-colors",
                      isSelected &&
                        "border-2 border-primary bg-primary/10 text-primary shadow-sm",
                      !isSelected &&
                        isPossible &&
                        "border border-neutral-300 bg-white text-neutral-800 hover:bg-neutral-50",
                      !isAvailable && isPossible && "opacity-70",
                      !isPossible &&
                        "cursor-not-allowed opacity-40 line-through",
                    )}
                    disabled={!isPossible}
                    key={val}
                    onClick={() => onSelect?.(def.name, val)}
                    role="radio"
                    type="button"
                    variant={isSelected ? "default" : "outline"}
                  >
                    <span>{optionLabel}</span>
                    {!isAvailable && isPossible && (
                      <span className="ml-1.5 text-[10px] uppercase tracking-wide text-neutral-500">
                        ({catalog.product.availability.unavailable})
                      </span>
                    )}
                  </Button>
                );
              })}
            </div>
          </fieldset>
        );
      })}
    </div>
  );
}
