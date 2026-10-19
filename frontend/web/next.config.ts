import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  // Pakiety współdzielone są konsumowane jako źródło TypeScript, bez kroku
  // budowania — patrz docs/adr/0005-pakiety-wspoldzielone-jako-zrodlo.md
  transpilePackages: ["@olivin/api", "@olivin/i18n", "@olivin/tokens"],

  typedRoutes: true,
};

export default withNextIntl(nextConfig);
