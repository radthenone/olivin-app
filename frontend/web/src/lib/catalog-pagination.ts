/**
 * Bezpiecznie parsuje numer strony z parametru query `page`.
 *
 * Args:
 *     pageParam: Wartość z searchParams.
 *
 * Returns:
 *     Numer strony jako liczba całkowita >= 1.
 */
export function parsePageNumber(pageParam?: string | string[]): number {
  const raw = Array.isArray(pageParam) ? pageParam[0] : pageParam;
  if (!raw) {
    return 1;
  }

  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed >= 1 ? parsed : 1;
}

/**
 * Wylicza łączną liczbę stron na podstawie liczby elementów i rozmiaru strony.
 *
 * Args:
 *     count: Łączna liczba elementów.
 *     pageSize: Rozmiar strony.
 *
 * Returns:
 *     Liczba stron, co najmniej 1.
 */
export function calculateTotalPages(count: number, pageSize: number): number {
  if (count <= 0 || pageSize <= 0) {
    return 1;
  }

  return Math.max(1, Math.ceil(count / pageSize));
}

/**
 * Buduje adres URL dla danej strony paginacji, zachowując istniejące filtry i parametry.
 *
 * Args:
 *     basePath: Ścieżka bazowa (np. `/pl/products`).
 *     pageNumber: Numer strony docelowej.
 *     searchParams: Bieżące parametry adresu (opcjonalnie).
 *
 * Returns:
 *     Adres URL ze zaktualizowanym parametrem `page`.
 */
export function buildPaginationHref(
  basePath: string,
  pageNumber: number,
  searchParams?:
    URLSearchParams | Record<string, string | string[] | undefined>,
): string {
  const params = new URLSearchParams();

  if (searchParams instanceof URLSearchParams) {
    searchParams.forEach((value, key) => {
      params.append(key, value);
    });
  } else if (searchParams) {
    for (const [key, value] of Object.entries(searchParams)) {
      if (value === undefined) continue;
      if (Array.isArray(value)) {
        for (const item of value) {
          params.append(key, item);
        }
      } else {
        params.set(key, value);
      }
    }
  }

  if (pageNumber > 1) {
    params.set("page", String(pageNumber));
  } else {
    params.delete("page");
  }

  const query = params.toString();
  return query ? `${basePath}?${query}` : basePath;
}
