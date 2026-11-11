import { useState } from "react";
import { Image, ScrollView, Text, View, Dimensions } from "react-native";
import { useTranslations } from "use-intl";
import type { ProductImage } from "@olivin/api/generated/apps/schemas";

export interface ProductGalleryProps {
  images: readonly ProductImage[];
  productName: string;
}

export function ProductGallery({ images, productName }: ProductGalleryProps) {
  const t = useTranslations("catalog");
  const [activeIndex, setActiveIndex] = useState(0);

  if (images.length === 0) {
    return (
      <View className="aspect-square w-full items-center justify-center rounded-2xl bg-neutral-100">
        <Text className="text-sm uppercase tracking-wider text-neutral-400">
          Olivin
        </Text>
      </View>
    );
  }

  return (
    <View className="w-full gap-3">
      <ScrollView
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={(e) => {
          const width = e.nativeEvent.layoutMeasurement.width;
          if (width > 0) {
            const index = Math.round(e.nativeEvent.contentOffset.x / width);
            setActiveIndex(index);
          }
        }}
        className="w-full rounded-2xl bg-neutral-100 overflow-hidden"
      >
        {images.map((image, index) => {
          const url =
            image.urls["800"] ??
            image.urls["400"] ??
            Object.values(image.urls)[0];
          const alt =
            image.altText ||
            t("accessibility.galleryImage", {
              index: index + 1,
              total: images.length,
              name: productName,
            });

          return (
            <View
              key={image.id ?? index}
              className="aspect-square w-full items-center justify-center"
              style={{ width: Dimensions.get("window").width - 32 }}
            >
              {url ? (
                <Image
                  accessibilityLabel={alt}
                  accessible
                  className="h-full w-full"
                  resizeMode="cover"
                  source={{ uri: url }}
                />
              ) : null}
            </View>
          );
        })}
      </ScrollView>

      {images.length > 1 && (
        <View className="flex-row justify-center gap-2 py-1">
          {images.map((_, index) => (
            <View
              key={index}
              className={`h-2 rounded-full transition-all ${
                index === activeIndex
                  ? "w-6 bg-brand-600"
                  : "w-2 bg-neutral-300"
              }`}
            />
          ))}
        </View>
      )}
    </View>
  );
}
