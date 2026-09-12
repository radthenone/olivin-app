import React, { type ComponentType } from "react";
import { selectPlatform } from "@core/config/platform";

type PlatformComponentMap<P> = {
  web?: ComponentType<P>;
  native?: ComponentType<P>;
  android?: ComponentType<P>;
  ios?: ComponentType<P>;
  default?: ComponentType<P>;
};

/**
 * Tworzy komponent z osobnymi implementacjami dla web/native.
 *
 * Dlaczego istnieje:
 * komponenty UI mogą mieć jedno publiczne API, ale różne szczegóły
 * interakcji lub layoutu na przeglądarce i urządzeniach natywnych.
 */
export function createPlatformComponent<P extends object>(
  map: PlatformComponentMap<P>,
  displayName?: string,
): ComponentType<P> {
  const selected = selectPlatform<ComponentType<P>>({
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
      "createPlatformComponent: podaj co najmniej web, native albo default.",
    );
  }

  const Wrapped: ComponentType<P> = (props: P) =>
    React.createElement(Impl, props);

  Wrapped.displayName =
    displayName ?? `Platform(${Impl.displayName ?? Impl.name ?? "Anonymous"})`;

  return Wrapped;
}
