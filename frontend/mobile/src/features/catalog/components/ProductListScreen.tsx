import { useCallback } from "react";
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  Text,
  View,
} from "react-native";
import { useTranslations } from "use-intl";
import { useRouter } from "expo-router";
import type { ProductList } from "@olivin/api/generated/apps/schemas";
import { useCatalogProductsInfinite } from "../hooks/use-catalog-products";
import { ProductTile } from "./ProductTile";
import { ProductErrorView } from "./ProductErrorView";
import { ProductListSkeleton } from "./ProductListSkeleton";

export function ProductListScreen() {
  const t = useTranslations("catalog");
  const router = useRouter();

  const {
    data,
    isLoading,
    isError,
    error,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
    refetch,
    isRefetching,
  } = useCatalogProductsInfinite();

  const products: ProductList[] =
    data?.pages.flatMap((page) => page?.results ?? []) ?? [];

  const handleEndReached = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const handleProductPress = useCallback(
    (product: ProductList) => {
      router.push({
        pathname: "/(app)/products/[slug]",
        params: { slug: product.slug },
      });
    },
    [router],
  );

  if (isLoading) {
    return <ProductListSkeleton count={6} />;
  }

  if (isError && products.length === 0) {
    return <ProductErrorView message={error?.message} onRetry={() => refetch()} />;
  }

  return (
    <View className="flex-1 bg-white">
      <FlatList
        contentContainerStyle={{ padding: 16, gap: 16 }}
        columnWrapperStyle={{ gap: 16 }}
        numColumns={2}
        data={products}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <ProductTile
            product={item}
            onPress={() => handleProductPress(item)}
          />
        )}
        onEndReached={handleEndReached}
        onEndReachedThreshold={0.5}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={() => refetch()}
            tintColor="#03453d"
          />
        }
        ListHeaderComponent={
          <View className="mb-2 gap-1">
            <Text className="text-2xl font-semibold text-brand-600">
              {t("list.title")}
            </Text>
            <Text className="text-sm text-neutral-600">
              {t("list.description")}
            </Text>
          </View>
        }
        ListEmptyComponent={
          <View className="items-center justify-center p-8">
            <Text className="text-base text-neutral-500">
              {t("list.empty")}
            </Text>
          </View>
        }
        ListFooterComponent={
          isFetchingNextPage ? (
            <View className="py-4">
              <ActivityIndicator color="#03453d" />
            </View>
          ) : null
        }
      />
    </View>
  );
}
