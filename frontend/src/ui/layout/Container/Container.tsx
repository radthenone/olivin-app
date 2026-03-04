import React from "react";
import { View, type ViewProps } from "react-native";
import { cn, isWeb } from "lib";
import type { Gap, ContainerStyleProps } from "./types";
import { containerVariants, type ContainerVariantProps } from "./variants";

const gapClass: Record<Gap, string> = {
  0: "gap-0",
  1: "gap-1",
  2: "gap-2",
  3: "gap-3",
  4: "gap-4",
  5: "gap-5",
  6: "gap-6",
  8: "gap-8",
  10: "gap-10",
  12: "gap-12",
  16: "gap-16",
};

export type ContainerProps = ViewProps &
  ContainerStyleProps &
  ContainerVariantProps & {
    className?: string;
  };

/** * Komponent Container to elastyczny kontener, który umożliwia łatwe zarządzanie układem dzieci.
 * Obsługuje różne platformy (Web, Native) oraz oferuje szeroki zakres opcji stylizacji, takich jak kierunek, wyrównanie, justowanie, zawijanie i odstępy między elementami.
 *
 * @param direction - Kierunek układu (row lub col)
 * @param platform - Platforma docelowa (web lub native)
 * @param align - Wyrównanie elementów w osi poprzecznej
 * @param justify - Justowanie elementów w osi głównej
 * @param wrap - Czy elementy mają się zawijać
 * @param gap - Odstęp między elementami
 * @param className - Dodatkowe klasy CSS
 * @param viewProps - Pozostałe właściwości przekazywane do komponentu View
 */
export function Container({
  direction = "col",
  platform,
  align,
  justify,
  wrap = false,
  gap = 0,
  className,
  ...viewProps
}: ContainerProps) {
  if (
    platform &&
    ((platform === "web" && !isWeb) || (platform === "native" && isWeb))
  ) {
    return null;
  }

  return (
    <View
      {...viewProps}
      className={cn(
        containerVariants({ direction, align, justify, wrap }),
        gapClass[gap],
        className,
      )}
    />
  );
}
