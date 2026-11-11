import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  // ADR 0034: strony katalogu są keszowane przez `"use cache"` i rewalidowane
  // tagami, a cena jest dziurą dynamiczną streamowaną w tym samym żądaniu.
  cacheComponents: true,
  partialPrefetching: true,

  // Pakiety współdzielone są konsumowane jako źródło TypeScript, bez kroku
  // budowania — patrz docs/adr/0005-pakiety-wspoldzielone-jako-zrodlo.md
  transpilePackages: [
    "@olivin/api",
    "@olivin/features",
    "@olivin/i18n",
    "@olivin/schemas",
    "@olivin/tokens",
  ],

  typedRoutes: true,

  // `next build` sprawdza typy razem z wygenerowanymi trasami, a testy typuje
  // osobno `tsc` w CI. Build produkcyjny sprawdza więc tylko kod aplikacji.
  typescript: {
    tsconfigPath:
      process.env.NODE_ENV === "production"
        ? "tsconfig.build.json"
        : "tsconfig.json",
  },

  /**
   * Allauth w trybie przeglądarkowym potrzebuje tych samych ciasteczek po
   * stronie webu: `sessionid` trzyma sesję, a `csrftoken` musi dać się odczytać
   * z `document.cookie`, żeby trafić do nagłówka `X-CSRFToken`. Proxy na tym
   * samym originie (Next → Django) spełnia oba warunki bez CORS.
   */
  async rewrites() {
    const backend = process.env.NEXT_PUBLIC_BACKEND_URL;

    if (!backend) {
      return [];
    }

    return [
      {
        source: "/_allauth/:path*",
        destination: `${backend.replace(/\/$/, "")}/_allauth/:path*`,
      },
    ];
  },
};

export default withNextIntl(nextConfig);
