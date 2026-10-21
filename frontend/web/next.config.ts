import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
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
