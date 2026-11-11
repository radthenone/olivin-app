import { Image, Pressable, Text, View } from "react-native";
import { useLocale, useTranslations } from "use-intl";
import type { ProductList } from "@olivin/api/generated/apps/schemas";
import { formatMoney } from "@olivin/money";

export interface ProductTileProps {
  product: ProductList;
  onPress: () => void;
}

/**
 * Kafelek produktu na liście mobilnej.
 *
 * Prezentuje zdjęcie główne z opisem dostępności, nazwę produktu oraz cenę
 * wyjściową najtańszego wariantu ("od X zł").
 */
export function ProductTile({ product, onPress }: ProductTileProps) {
  const t = useTranslations("catalog");
  const locale = useLocale();

  const primaryImage =
    product.cheapestVariant?.images?.find((img) => img.isPrimary) ??
    product.cheapestVariant?.images?.[0];

  const imageUrl = primaryImage
    ? primaryImage.urls["400"] ??
      primaryImage.urls["800"] ??
      Object.values(primaryImage.urls)[0]
    : undefined;

  const imageAlt =
    primaryImage?.altText ||
    t("accessibility.productImage", { name: product.name });

  const formattedPrice = product.cheapestVariant?.price
    ? formatMoney(product.cheapestVariant.price, locale)
    : null;

  return (
    <Pressable
      accessibilityLabel={`${product.name}, ${
        formattedPrice ? t("card.fromPrice", { price: formattedPrice }) : ""
      }`}
      accessibilityRole="button"
      className="flex-1 rounded-xl border border-neutral-200 bg-white p-3 shadow-xs active:opacity-90"
      onPress={onPress}
    >
      <View className="aspect-square w-full items-center justify-center overflow-hidden rounded-lg bg-neutral-100">
        {imageUrl ? (
          <Image
            accessibilityLabel={imageAlt}
            accessible
            className="h-full w-full"
            resizeMode="cover"
            source={{ uri: imageUrl }}
          />
        ) : (
          <Text className="text-xs uppercase tracking-wider text-neutral-400">
            Olivin
          </Text>
        )}
      </View>

      <View className="mt-3 gap-1">
        <Text
          className="text-base font-medium text-neutral-900"
          numberOfLines={2}
        >
          {product.name}
        </Text>
        {formattedPrice && (
          <Text className="text-sm font-semibold text-brand-600">
            {t("card.fromPrice", { price: formattedPrice })}
          </Text>
        )}
      </View>
    </Pressable>
  );
}
