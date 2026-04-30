/**
 * Fetch client obsługuje auth bezpośrednio w `@http/client`.
 *
 * Eksport zostaje, żeby starsze importy nie łamały kompilacji w trakcie
 * porządkowania warstwy API.
 */
export function setupAuthInterceptor(): { request: number; response: number } {
  return { request: -1, response: -1 };
}
