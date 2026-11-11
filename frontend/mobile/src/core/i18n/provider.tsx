import { useEffect, useState, type PropsWithChildren } from "react";
import { IntlProvider } from "use-intl";
import { defaultLocale, messages, type Locale } from "@olivin/i18n";
import { getActiveLocale, subscribeLocale } from "./locale";
import { setupIntlPolyfills } from "./polyfills";

setupIntlPolyfills();

/**
 * Dostarcza kontekst i18n (`use-intl`) dla całej aplikacji mobilnej.
 *
 * Wykorzystuje wspólny katalog komunikatów ICU z pakietu `@olivin/i18n` (ADR 0035).
 */
export function AppIntlProvider({
  children,
  initialLocale,
}: PropsWithChildren<{ initialLocale?: Locale }>) {
  const [locale, setLocale] = useState<Locale>(
    initialLocale ?? getActiveLocale() ?? defaultLocale,
  );

  useEffect(() => {
    return subscribeLocale((next) => {
      setLocale(next);
    });
  }, []);

  return (
    <IntlProvider
      key={locale}
      locale={locale}
      messages={messages[locale]}
      timeZone="Europe/Warsaw"
    >
      {children}
    </IntlProvider>
  );
}
