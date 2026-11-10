import type { ProductDetail } from "@olivin/api/generated/apps/schemas";
import { getProductsRetrieveUrl } from "@olivin/api/generated/apps/products/products";
import type { Locale } from "@olivin/i18n";
import { cacheLife, cacheTag } from "next/cache";
import { cookies } from "next/headers";

/**
 * Publiczny transport serwerowy katalogu (ADR 0034).
 *
 * Komponenty serwerowe katalogu nie mogą czytać cookies sesji, bo ich wynik
 * trafia do wspólnego kesza. Dlatego katalog rozmawia z backendem osobnym
 * adresem ze zmiennej `CATALOG_API_URL` (fallback: publiczny adres backendu)
 * i bez poświadczeń przeglądarki. Ten sam adres jest szwem testowym: w CI
 * wskazuje stub, a przy `E2E_LIVE_BACKEND=1` prawdziwy backend.
 */

/** Cookie waluty z kraju dostawy (ADR 0035). Brak cookie oznacza złote. */
export const currencyCookieName = "currency";

export type CatalogCurrency = "PLN" | "EUR";

function catalogBaseUrl(): string {
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

async function fetchProduct(
  slug: string,
  locale: Locale,
  currency?: CatalogCurrency,
): Promise<ProductDetail | null> {
  const url = getProductsRetrieveUrl(slug, {
    lang: locale,
    ...(currency ? { currency } : {}),
  });
  const response = await fetch(`${catalogBaseUrl()}${url}`, {
    headers: { accept: "application/json" },
  });

  // Zdjęty albo nieistniejący produkt to 404 strony, nie błąd katalogu.
  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Katalog odpowiedział statusem ${response.status}.`);
  }

  return (await response.json()) as ProductDetail;
}

/**
 * Produkt do keszowanej części karty.
 *
 * Args:
 *     slug: Stały slug produktu.
 *     locale: Język treści z prefiksu adresu.
 *
 * Returns:
 *     Produkt albo `null`, gdy backend zwrócił 404.
 */
export async function getProductForPage(
  slug: string,
  locale: Locale,
): Promise<ProductDetail | null> {
  "use cache";
  // Zapisy produktu i przeliczenie cen unieważniają tag z ADR 0034.
  cacheTag(`product:${slug}`);
  // Krótkie wygasanie jako siatka bezpieczeństwa, gdy rewalidacja nie dojdzie.
  cacheLife("minutes");

  return fetchProduct(slug, locale);
}

/**
 * Produkt z ceną w walucie cookie — dynamiczna dziura, nigdy nie keszowana.
 *
 * Args:
 *     slug: Stały slug produktu.
 *     locale: Język treści z prefiksu adresu.
 *     currency: Waluta z cookie; `PLN`, gdy cookie nie ma albo jest inne.
 *
 * Returns:
 *     Produkt z przeliczonymi cenami albo `null` przy 404.
 */
export async function getProductPrice(
  slug: string,
  locale: Locale,
  currency: CatalogCurrency,
): Promise<ProductDetail | null> {
  return fetchProduct(slug, locale, currency);
}

/**
 * Waluta bieżącego żądania. Waluta nie trafia do adresu ani do kesza.
 *
 * Returns:
 *     `EUR` tylko przy jawnym cookie euro; inaczej `PLN`.
 */
export async function getRequestCurrency(): Promise<CatalogCurrency> {
  const value = (await cookies()).get(currencyCookieName)?.value;

  return value === "EUR" ? "EUR" : "PLN";
}
