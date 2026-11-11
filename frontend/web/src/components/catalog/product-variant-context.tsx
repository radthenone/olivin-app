"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import type { ProductVariant } from "@olivin/api/generated/apps/schemas";

type ProductVariantContextValue = {
  selectedVariant: ProductVariant | null;
  setSelectedVariant: (variant: ProductVariant | null) => void;
};

const ProductVariantContext = createContext<ProductVariantContextValue | null>(
  null,
);

/**
 * Kontekst wybranego wariantu na karcie produktu.
 *
 * Łączy interaktywną wyspę wyboru wariantu z galerią zdjęć, dzięki czemu
 * zmiana wariantu automatycznie przełącza zdjęcia bez konieczności
 * przekazywania callbacków w dół drzewa komponentów serwerowych.
 */
export function ProductVariantProvider({
  initialVariant = null,
  children,
}: {
  initialVariant?: ProductVariant | null;
  children: ReactNode;
}) {
  const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(
    initialVariant,
  );

  return (
    <ProductVariantContext.Provider
      value={{ selectedVariant, setSelectedVariant }}
    >
      {children}
    </ProductVariantContext.Provider>
  );
}

/**
 * Hook dostępu do wybranego wariantu produktu.
 *
 * Returns:
 *     Wartość kontekstu z aktualnym wariantem i setterem.
 */
export function useProductVariant(): ProductVariantContextValue {
  const context = useContext(ProductVariantContext);
  if (!context) {
    return {
      selectedVariant: null,
      setSelectedVariant: () => {},
    };
  }
  return context;
}
