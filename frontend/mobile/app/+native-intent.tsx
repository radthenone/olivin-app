type NativeIntent = {
  path: string;
  initial: boolean;
};

/**
 * Przepisuje techniczne deep linki zanim trafią do Expo Router.
 */
export function redirectSystemPath({ path }: NativeIntent): string {
  try {
    const url = new URL(path, "frontend://app");

    const callbackNames = ["authredirect", "oauthredirect", "authorize"];

    if (
      callbackNames.includes(url.hostname) ||
      callbackNames.includes(url.pathname.replace("/", ""))
    ) {
      return "/authredirect";
    }

    return path;
  } catch {
    if (
      path.includes("authredirect") ||
      path.includes("oauthredirect") ||
      path.includes("authorize")
    ) {
      return "/authredirect";
    }

    return path;
  }
}
