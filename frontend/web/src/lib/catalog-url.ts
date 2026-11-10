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
