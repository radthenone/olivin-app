import { ScrollView, Text, View } from "react-native";
import { useLocale, useTranslations } from "use-intl";
import type { ProductDetail } from "@olivin/api/generated/apps/schemas";
import {
  getAvailabilityCategory,
  uniqueStones,
  useVariantSelection,
} from "@olivin/features/catalog";
import { formatMoney } from "@olivin/money";
import { ProductGallery } from "./ProductGallery";
import { MobileVariantSelector } from "./MobileVariantSelector";

export interface ProductDetailViewProps {
  product: ProductDetail;
}

export function ProductDetailView({ product }: ProductDetailViewProps) {
  const t = useTranslations("catalog");
  const locale = useLocale();

  const { selectedAttributes, selectedVariant, selectAttribute } =
    useVariantSelection({
      variants: product.variants,
    });

  const activeVariant = selectedVariant ?? product.variants[0];
  const availabilityCategory = activeVariant
    ? getAvailabilityCategory(activeVariant)
    : "unavailable";

  const stones = uniqueStones(product.variants);
  const activeImages =
    activeVariant?.images && activeVariant.images.length > 0
      ? activeVariant.images
      : product.images;

  return (
    <ScrollView
      contentContainerStyle={{ padding: 16, gap: 24, paddingBottom: 48 }}
      className="flex-1 bg-white"
    >
      <View className="gap-2">
        <Text className="text-2xl font-bold text-brand-600">
          {product.name}
        </Text>
        {product.averageRating !== null && (
          <Text className="text-sm font-medium text-neutral-600">
            {t("product.rating", { rating: product.averageRating })}
          </Text>
        )}
      </View>

      <ProductGallery images={activeImages} productName={product.name} />

      {activeVariant && (
        <View className="rounded-xl border border-neutral-200 bg-neutral-50 p-4 gap-2">
          <View className="flex-row items-baseline justify-between">
            <Text className="text-2xl font-bold text-neutral-900">
              {formatMoney(activeVariant.price, locale)}
            </Text>
            <Text
              className={`text-sm font-semibold ${
                availabilityCategory === "available"
                  ? "text-success-700"
                  : availabilityCategory === "lowStock"
                    ? "text-warning-700"
                    : "text-danger-700"
              }`}
            >
              {t(`product.availability.${availabilityCategory}`)}
            </Text>
          </View>

          <MobileVariantSelector
            onSelect={selectAttribute}
            selectedAttributes={selectedAttributes}
            variants={product.variants}
          />

          {product.isEngravable && product.engravingPrice !== null && (
            <View className="border-t border-neutral-200 pt-3 mt-1">
              <Text className="text-xs text-neutral-600">
                {t("product.engravingAvailable", {
                  price: formatMoney(product.engravingPrice, locale),
                })}
              </Text>
            </View>
          )}
        </View>
      )}

      <View className="gap-2">
        <Text className="text-lg font-semibold text-neutral-900">
          {t("product.description")}
        </Text>
        <Text className="text-base leading-relaxed text-neutral-700">
          {product.description}
        </Text>
      </View>

      <View className="gap-3 rounded-xl border border-neutral-200 p-4 bg-white">
        <View className="flex-row justify-between py-1 border-b border-neutral-100">
          <Text className="text-sm text-neutral-500">
            {t("product.material")}
          </Text>
          <Text className="text-sm font-medium text-neutral-800">
            {t(`material.${product.material}`)}
          </Text>
        </View>

        <View className="flex-row justify-between py-1 border-b border-neutral-100">
          <Text className="text-sm text-neutral-500">
            {t("product.fineness")}
          </Text>
          <Text className="text-sm font-medium text-neutral-800">
            {product.fineness}
          </Text>
        </View>

        {stones.length > 0 && (
          <View className="flex-row justify-between py-1 border-b border-neutral-100">
            <Text className="text-sm text-neutral-500">
              {t("product.stones")}
            </Text>
            <Text className="text-sm font-medium text-neutral-800">
              {stones.map((s) => t(`stone.${s}`)).join(", ")}
            </Text>
          </View>
        )}

        {product.isMadeToOrder && product.productionTimeDays !== null && (
          <View className="flex-row justify-between py-1">
            <Text className="text-sm text-neutral-500">
              {t("product.productionTime", {
                days: product.productionTimeDays,
              })}
            </Text>
          </View>
        )}
      </View>
    </ScrollView>
  );
}
