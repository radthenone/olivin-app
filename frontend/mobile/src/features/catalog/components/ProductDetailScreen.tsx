import { ActivityIndicator, Text, View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { useTranslations } from "use-intl";
import { colors } from "@olivin/tokens";
import { useCatalogProduct } from "../hooks/use-catalog-product";
import { ProductDetailView } from "./ProductDetailView";
import { ProductErrorView } from "./ProductErrorView";

export function ProductDetailScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const t = useTranslations("catalog");
  const {
    data: product,
    isLoading,
    isError,
    error,
    refetch,
  } = useCatalogProduct(slug);

  if (isLoading) {
    return (
      <View className="flex-1 items-center justify-center bg-white p-6">
        <ActivityIndicator color={colors.brand[600]} size="large" />
      </View>
    );
  }

  if (isError) {
    return <ProductErrorView error={error} onRetry={() => refetch()} />;
  }

  if (!product) {
    return (
      <View className="flex-1 items-center justify-center bg-white p-6 gap-3">
        <Text className="text-xl font-semibold text-neutral-800">
          {t("product.notFound.title")}
        </Text>
        <Text className="text-center text-sm text-neutral-600">
          {t("product.notFound.description")}
        </Text>
      </View>
    );
  }

  return <ProductDetailView product={product} />;
}
