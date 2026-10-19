/**
 * Matcher proxy'ego języka.
 *
 * Poza routingiem językowym zostają adresy techniczne: `/api/*`
 * (kontrakt rewalidacji z ADR 0034), `/.well-known/*`, `robots.txt`,
 * `sitemap.xml`, zasoby Next i pliki statyczne. Pliki statyczne poznajemy po
 * kropce w ścieżce, tak jak w dokumentacji next-intl.
 */
export const localeMatcher = "/((?!api|trpc|_next|_vercel|.*\\..*).*)";

const localeMatcherPattern = new RegExp(`^${localeMatcher}$`);

/** Czy ścieżka należy do stron sklepu, czyli do przekierowania na prefiks? */
export function matchesLocaleRouting(pathname: string): boolean {
  return localeMatcherPattern.test(pathname);
}
