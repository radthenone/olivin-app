/**
 * Adres publicznego API katalogu (ADR 0034).
 *
 * Ze zmiennej `CATALOG_API_URL` (fallback: publiczny adres backendu). Ten sam
 * adres jest szwem testowym: w CI wskazuje stub, a przy `E2E_LIVE_BACKEND=1`
 * prawdziwy backend.
 *
 * Returns:
 *     Adres bez końcowego ukośnika.
 */
export function catalogBaseUrl(): string {
  const configured =
    process.env.CATALOG_API_URL ?? process.env.NEXT_PUBLIC_BACKEND_URL;

  if (!configured) {
    throw new Error(
      "Brak CATALOG_API_URL. Bez adresu backendu katalog nie ma skąd pobrać " +
        "produktów.",
    );
  }

  return configured.replace(/\/$/, "");
}

/** Format sluga produktu: `SlugField` Django bez `allow_unicode`. */
const PRODUCT_SLUG = /^[-a-zA-Z0-9_]+$/;

/**
 * Czy slug można wstawić do adresu API katalogu.
 *
 * To format `validate_slug` z `backend/src/apps/products/models/product.py`.
 * Sprawdzamy slug w surowej postaci, więc `/`, `.` i znaki spoza ASCII (także
 * zakodowane procentem) nie przechodzą: ani `a%2Fb` z adresu w proxy, ani
 * `../x.y` ze zdekodowanego parametru trasy nie zmienią ścieżki żądania.
 *
 * Moduł nie importuje `next/*`, bo korzysta z niego `proxy.ts`.
 *
 * Args:
 *     slug: Slug z adresu żądania albo z parametru trasy.
 *
 * Returns:
 *     `true`, gdy slug ma format sluga produktu.
 */
export function isProductSlug(slug: string): boolean {
  return PRODUCT_SLUG.test(slug);
}
