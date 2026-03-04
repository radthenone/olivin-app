import React from "react";
import { Platform } from "react-native";
import type { ComponentType, ReactNode } from "react";
import { ps } from "./ps";

type PlatformComponentMap<P> = {
  web?: ComponentType<P>;
  native?: ComponentType<P>;
  android?: ComponentType<P>;
  ios?: ComponentType<P>;
  default?: ComponentType<P>;
};

/**
 * Buduje komponent wybierający implementację zależnie od platformy.
 *
 * Cel: jedno publiczne API komponentu + osobne implementacje web/native,
 * bez rozrzucania `Platform.OS` po kodzie i bez plików `.web/.native`.
 *
 * Przykład:
 * ```tsx
 * import React from "react";
 * import { Text, Pressable } from "react-native";
 * import { Link, useRouter } from "expo-router";
 * import { createPlatformComponent, cn } from "lib";
 *
 * type Props = { href: string; children: React.ReactNode };
 *
 * const linkClass = cn("text-sm underline");
 *
 * function LinkWeb({ href, children }: Props) {
 *   return (
 *     <Link href={href}>
 *       <Text className={linkClass}>{children}</Text>
 *     </Link>
 *   );
 * }
 *
 * function LinkNative({ href, children }: Props) {
 *   const router = useRouter();
 *   return (
 *     <Pressable onPress={() => router.push(href)}>
 *       <Text className={linkClass}>{children}</Text>
 *     </Pressable>
 *   );
 * }
 *
 * export const SmartLink = createPlatformComponent<Props>(
 *   { web: LinkWeb, native: LinkNative },
 *   "SmartLink",
 * );
 * ```
 */
export function createPlatformComponent<P extends object>(
  map: PlatformComponentMap<P>,
  displayName?: string,
): ComponentType<P> {
  const selected = ps<ComponentType<P>>({
    web: map.web,
    android: map.android ?? map.native,
    ios: map.ios ?? map.native,
    native: map.native,
    default: map.default,
  });

  const fallback =
    map.default ?? map.native ?? map.web ?? map.android ?? map.ios;

  const Impl = selected ?? fallback;

  if (!Impl) {
    throw new Error(
      "createPlatformComponent: missing implementation (provide at least one of web/native/default)",
    );
  }

  const Wrapped: ComponentType<P> = (props: P) =>
    React.createElement(Impl as any, props as any);
  Wrapped.displayName =
    displayName ?? `Platform(${Impl.displayName ?? Impl.name ?? "Anonymous"})`;

  return Wrapped;
}

type PlatformNodeMap = {
  web?: ReactNode;
  native?: ReactNode;
  android?: ReactNode;
  ios?: ReactNode;
  default?: ReactNode;
};

/**
 * Zwraca fragment JSX zależnie od platformy.
 * Przydatne, gdy różni się tylko kawałek layoutu.
 */
export function platformRender(nodes: PlatformNodeMap): ReactNode {
  return (
    ps<ReactNode>({
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

export function Web({ children }: { children: ReactNode }) {
  return Platform.OS === "web" ? <>{children}</> : null;
}

export function Native({ children }: { children: ReactNode }) {
  return Platform.OS === "web" ? null : <>{children}</>;
}
