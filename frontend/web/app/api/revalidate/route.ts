import { type NextRequest } from "next/server";

import { handleRevalidateRequest } from "@/lib/revalidate";

/**
 * Punkt końcowy rewalidacji keszu katalogu na webie (ADR 0034, #318, #358).
 *
 * Backend po zapisie produktu (tag `product:<slug>`) oraz po przeliczeniu cen
 * lub publikacji (tag `catalog`) wywołuje to żądanie z nagłówkiem
 * `X-Revalidate-Secret`. Wywołanie bez poprawnego sekretu jest odrzucane (401),
 * a niepoprawna treść payloadu zwraca 400.
 *
 * Args:
 *     request: Żądanie HTTP z Next.js.
 *
 * Returns:
 *     Odpowiedź HTTP z potwierdzeniem rewalidacji lub błędem.
 */
export async function POST(request: NextRequest): Promise<Response> {
  return handleRevalidateRequest(request);
}
