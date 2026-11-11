import { Pressable, Text, View } from "react-native";
import { useTranslations } from "use-intl";
import type { ProductVariant } from "@olivin/api/generated/apps/schemas";
import {
  getAttributeDefinitions,
  isOptionAvailable,
  type VariantAttributeName,
  type VariantSelection,
} from "@olivin/features/catalog";

export interface MobileVariantSelectorProps {
  variants: readonly ProductVariant[];
  selectedAttributes: VariantSelection;
  onSelect: (name: VariantAttributeName, value: string) => void;
}

export function MobileVariantSelector({
  variants,
  selectedAttributes,
  onSelect,
}: MobileVariantSelectorProps) {
  const t = useTranslations("catalog");
  const definitions = getAttributeDefinitions(variants);

  if (definitions.length === 0) {
    return null;
  }

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

  return (
    <View className="gap-5">
      {definitions.map((def) => {
        const groupLabel = t(`product.attributes.${def.name}`);
        const currentVal = selectedAttributes[def.name];

        if (def.values.length === 1) {
          return (
            <View key={def.name} className="flex-row items-center gap-2">
              <Text className="text-sm font-medium text-neutral-800">
                {groupLabel}:
              </Text>
              <Text className="text-sm text-neutral-700">
                {optionLabel(def.name, def.values[0] as string)}
              </Text>
            </View>
          );
        }

        return (
          <View key={def.name} className="gap-2">
            <Text className="text-sm font-medium text-neutral-800">
              {groupLabel}
            </Text>
            <View className="flex-row flex-wrap gap-2">
              {def.values.map((val) => {
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
                  <Pressable
                    key={val}
                    accessibilityLabel={
                      isAvailable ? label : `${label} (${unavailable})`
                    }
                    accessibilityRole="radio"
                    accessibilityState={{ selected: isSelected }}
                    className={`flex-row items-center rounded-lg border px-3.5 py-2 ${
                      isSelected
                        ? "border-brand-600 bg-brand-50"
                        : "border-neutral-300 bg-white active:bg-neutral-50"
                    }`}
                    onPress={() => onSelect(def.name, val)}
                  >
                    <Text
                      className={`text-sm font-medium ${
                        isSelected ? "text-brand-700" : "text-neutral-800"
                      }`}
                    >
                      {label}
                    </Text>
                    {!isAvailable && (
                      <Text className="ml-1 text-xs text-neutral-400">
                        ({unavailable})
                      </Text>
                    )}
                  </Pressable>
                );
              })}
            </View>
          </View>
        );
      })}
    </View>
  );
}
