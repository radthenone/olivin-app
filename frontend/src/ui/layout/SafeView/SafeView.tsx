import React from "react";
import { View, type ViewProps } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { cn } from "lib";

type Edge = "top" | "bottom" | "left" | "right";

export interface SafeViewProps extends ViewProps {
  children: React.ReactNode;
  edges?: Edge[];
  className?: string;
}

/**
 * Komponent SafeView to wrapper ekranu uwzględniający bezpieczne obszary urządzenia.
 * Domyślnie dodaje padding tylko dla górnej i dolnej krawędzi (notch, navigation bar).
 *
 * @param edges - Krawędzie, dla których ma być dodany padding (domyślnie ["top", "bottom"])
 * @param className - Dodatkowe klasy CSS
 * @param children - Zawartość ekranu
 */
export function SafeView({
  children,
  edges = ["top", "bottom", "left", "right"],
  className,
  style,
  ...props
}: SafeViewProps) {
  const insets = useSafeAreaInsets();

  return (
    <View
      style={[
        {
          flex: 1,
          paddingTop: edges.includes("top") ? insets.top : 0,
          paddingBottom: edges.includes("bottom") ? insets.bottom : 0,
          paddingLeft: edges.includes("left") ? insets.left : 0,
          paddingRight: edges.includes("right") ? insets.right : 0,
        },
        style,
      ]}
      className={cn("flex-1", className)}
      {...props}
    >
      {children}
    </View>
  );
}
