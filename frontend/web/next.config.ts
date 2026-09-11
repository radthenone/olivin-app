import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pakiety współdzielone są konsumowane jako źródło TypeScript, bez kroku
  // budowania — patrz docs/adr/0005-pakiety-wspoldzielone-jako-zrodlo.md
  transpilePackages: ["@olivin/api", "@olivin/tokens"],

  typedRoutes: true,
};

export default nextConfig;
