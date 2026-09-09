import type { PropsWithChildren } from "react";
import { View, type ViewProps } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { cn } from "@core/styles/cn";

type Edge = "top" | "bottom" | "left" | "right";

type SafeViewProps = PropsWithChildren<
  ViewProps & {
    edges?: Edge[];
    className?: string;
  }
>;

/**
 * Kontener uwzględniający bezpieczne obszary ekranu na native.
 *
 * Dlaczego istnieje:
 * stary działający layout owijał stack na Androidzie w taki wrapper,
 * co stabilizuje pozycjonowanie treści i natywnych overlayów Expo.
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
      className={cn("flex-1", className)}
      style={[
        {
          flex: 1,
          backgroundColor: "#ffffff",
          paddingTop: edges.includes("top") ? insets.top : 0,
          paddingBottom: edges.includes("bottom") ? insets.bottom : 0,
          paddingLeft: edges.includes("left") ? insets.left : 0,
          paddingRight: edges.includes("right") ? insets.right : 0,
        },
        style,
      ]}
      {...props}
    >
      {children}
    </View>
  );
}
