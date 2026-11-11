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
 */
export function calculateTotalPages(count: number, pageSize: number): number {
  if (count <= 0 || pageSize <= 0) {
    return 1;
  }

  return Math.max(1, Math.ceil(count / pageSize));
}
