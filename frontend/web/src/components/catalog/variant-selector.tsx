"use client";

import type { KeyboardEvent } from "react";
import { useTranslations } from "next-intl";
import type { ProductVariant } from "@olivin/api/generated/apps/schemas";
import {
  getAttributeDefinitions,
  isOptionAvailable,
  type AttributeDefinition,
  type VariantAttributeName,
  type VariantSelection,
} from "@olivin/features/catalog";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/** Kierunek przesunięcia fokusu w grupie radio dla danej strzałki. */
const ARROW_STEP: Record<string, 1 | -1> = {
  ArrowRight: 1,
  ArrowDown: 1,
  ArrowLeft: -1,
  ArrowUp: -1,
};

/**
 * Przełącznik wariantów dostępny z klawiatury i czytnika ekranu.
 *
 * Każdy atrybut z wieloma wartościami to grupa `radiogroup` z jednym punktem Tab
 * (zaznaczona opcja) i przesuwaniem strzałkami. Opcje nie są blokowane: kliknięcie
 * kombinacji, której nie ma w katalogu, przeskakuje do najbliższego istniejącego
 * wariantu, a wariant wyprzedany jest oznaczony jako niedostępny. Atrybut z jedną
 * wartością jest pokazany tylko do odczytu.
 */
export function VariantSelector({
  variants,
  selectedAttributes,
  onSelect,
}: {
  variants: readonly ProductVariant[];
  selectedAttributes: VariantSelection;
  onSelect?: (name: VariantAttributeName, value: string) => void;
}) {
  const t = useTranslations("catalog");
  const definitions = getAttributeDefinitions(variants);

  if (definitions.length === 0) {
    return null;
  }

  /** Czytelna etykieta wartości atrybutu; nieznana wartość wraca bez zmian. */
  function optionLabel(name: VariantAttributeName, value: string): string {
    if (value === "") {
      return t("product.attributeNone");
    }

    if (name === "metalColor" || name === "stone") {
      const key = `${name}.${value}` as Parameters<typeof t.has>[0];
      return t.has(key) ? t(key) : value;
    }

    if (name === "length") {
      return t("product.lengthValue", { value });
    }

    return value;
  }

  function handleKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    def: AttributeDefinition,
    index: number,
  ) {
    const step = ARROW_STEP[event.key];
    if (step === undefined) {
      return;
    }

    event.preventDefault();
    const nextIndex = (index + step + def.values.length) % def.values.length;
    onSelect?.(def.name, def.values[nextIndex] as string);
    event.currentTarget.parentElement
      ?.querySelectorAll<HTMLElement>('[role="radio"]')
      [nextIndex]?.focus();
  }

  return (
    <div className="flex flex-col gap-5">
      {definitions.map((def) => {
        const groupLabel = t(`product.attributes.${def.name}`);
        const currentVal = selectedAttributes[def.name];

        if (def.values.length === 1) {
          return (
            <p className="text-sm text-neutral-700" key={def.name}>
              <span className="font-medium text-neutral-800">
                {groupLabel}:
              </span>{" "}
              {optionLabel(def.name, def.values[0] as string)}
            </p>
          );
        }

        const hasSelected =
          currentVal !== undefined && def.values.includes(currentVal);

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
              {def.values.map((val, index) => {
                const isSelected = currentVal === val;
                const isAvailable = isOptionAvailable(
                  variants,
                  selectedAttributes,
                  def.name,
                  val,
                );
                const label = optionLabel(def.name, val);
                const unavailable = t("product.availability.unavailable");

                return (
                  <Button
                    aria-checked={isSelected}
                    aria-label={
                      isAvailable ? label : `${label} (${unavailable})`
                    }
                    className={cn(
                      "relative h-9 px-3.5 text-xs font-medium transition-colors",
                      isSelected &&
                        "border-2 border-primary bg-primary/10 text-primary shadow-sm",
                      !isSelected &&
                        "border border-neutral-300 bg-neutral-0 text-neutral-800 hover:bg-neutral-50",
                    )}
                    key={val}
                    onClick={() => onSelect?.(def.name, val)}
                    onKeyDown={(event) => handleKeyDown(event, def, index)}
                    role="radio"
                    tabIndex={(hasSelected ? isSelected : index === 0) ? 0 : -1}
                    type="button"
                    variant={isSelected ? "default" : "outline"}
                  >
                    <span>{label}</span>
                    {!isAvailable && (
                      <span className="ml-1.5 text-xs uppercase tracking-wide text-neutral-500">
                        ({unavailable})
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
