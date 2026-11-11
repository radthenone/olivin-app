"use client";

import type { ProductImage } from "@olivin/api/generated/apps/schemas";

import { useProductVariant } from "./product-variant-context";

/**
 * Galeria zdjęć na karcie produktu.
 *
 * Wyświetla zdjęcia powiązane z aktualnie wybranym wariantem (np. odpowiedni kolor złota).
 * Jeśli dany wariant nie definiuje własnych zdjęć, wraca do domyślnych zdjęć produktu.
 */
export function ProductGallery({
  defaultImages,
}: {
  defaultImages: readonly ProductImage[];
}) {
  const { selectedVariant } = useProductVariant();

  const variantImages =
    selectedVariant?.images && selectedVariant.images.length > 0
      ? selectedVariant.images
      : defaultImages;

  return (
    <div className="flex flex-col gap-3">
      {variantImages.map((image) => {
        const url =
          image.urls["800"] ??
          image.urls["400"] ??
          Object.values(image.urls)[0];

        if (!url) {
          return null;
        }

        return (
          // Zdjęcia katalogu przychodzą z backendu o zmiennym adresie, więc
          // optymalizator Next nie zna ich z góry.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            alt={image.altText}
            className="w-full rounded-xl border border-neutral-200 object-cover"
            height={800}
            key={image.id}
            src={url}
            width={800}
          />
        );
      })}
    </div>
  );
}
