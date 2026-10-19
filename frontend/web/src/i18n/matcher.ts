/**
 * Matcher proxy'ego języka.
 *
 * Poza routingiem językowym zostają adresy techniczne: `/api` i `/api/*`
 * (kontrakt rewalidacji z ADR 0034), `/_next/*`, `/.well-known/*`,
 * `robots.txt`, `sitemap.xml` i pliki statyczne (kropka w ostatnim segmencie).
 * Lookahead kotwiczy cały segment, żeby `/apiary` czy `/api-docs` nadal
 * dostawały prefiks języka.
 */
export const localeMatcher =
  "/((?!api(?:/|$)|_next/|\\.well-known/|robots\\.txt$|sitemap\\.xml$|.*\\.[^/]+$).*)";

const localeMatcherPattern = new RegExp(`^${localeMatcher}$`);

/** Czy ścieżka należy do stron sklepu, czyli do przekierowania na prefiks? */
export function matchesLocaleRouting(pathname: string): boolean {
  return localeMatcherPattern.test(pathname);
}
