import { type ReactNode } from "react";
import { Platform } from "react-native";
import { selectPlatform } from "@core/config/platform";

type PlatformNodeMap = {
  web?: ReactNode;
  native?: ReactNode;
  android?: ReactNode;
  ios?: ReactNode;
  default?: ReactNode;
};

/**
 * Zwraca fragment JSX zależnie od aktualnej platformy.
 *
 * Dlaczego istnieje:
 * małe różnice w ekranach nie powinny wymagać osobnych plików `.web`
 * i `.native`, jeśli różni się tylko pojedynczy fragment UI.
 */
export function platformRender(nodes: PlatformNodeMap): ReactNode {
  return (
    selectPlatform<ReactNode>({
      web: nodes.web,
      android: nodes.android ?? nodes.native,
      ios: nodes.ios ?? nodes.native,
      native: nodes.native,
      default: nodes.default,
    }) ??
    nodes.default ??
    null
  );
}

/**
 * Renderuje dzieci wyłącznie w przeglądarce.
 */
export function WebOnly({ children }: { children: ReactNode }) {
  return Platform.OS === "web" ? <>{children}</> : null;
}

/**
 * Renderuje dzieci wyłącznie na platformach natywnych.
 */
export function NativeOnly({ children }: { children: ReactNode }) {
  return Platform.OS === "web" ? null : <>{children}</>;
}
