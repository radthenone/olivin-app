import type { PropsWithChildren } from "react";
import { View } from "react-native";
import { cn } from "@core/styles/cn";

type ScreenProps = PropsWithChildren<{
  className?: string;
}>;

/**
 * Bazowy kontener ekranu.
 *
 * Dlaczego istnieje:
 * każdy ekran powinien mieć spójny padding, tło i zachowanie layoutu.
 */
export function Screen({ children, className }: ScreenProps) {
  return (
    <View
      className={cn("flex-1 bg-white px-4 py-6", className)}
      style={{ backgroundColor: "#ffffff" }}
    >
      {children}
    </View>
  );
}
