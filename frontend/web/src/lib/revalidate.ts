import { createHash, timingSafeEqual } from "node:crypto";
import { revalidateTag } from "next/cache";

/** Nagłówek HTTP z sekretem rewalidacji (ADR 0034, #318). */
export const REVALIDATE_SECRET_HEADER = "x-revalidate-secret";

/**
 * Porównuje sekret rewalidacji w stałym czasie, zapobiegając atakom czasowym.
 *
 * Używa skrótu SHA-256 obu wartości przed `timingSafeEqual`, co gwarantuje
 * identyczną długość buforów (32 bajty) i stały czas porównania niezależnie
 * od długości podanego sekretu.
 *
 * Args:
 *     providedSecret: Wartość z nagłówka żądania.
 *     expectedSecret: Wartość ze zmiennej środowiskowej REVALIDATE_SECRET.
 *
 * Returns:
 *     `true`, gdy oba sekrety są niepuste i identyczne.
 */
export function verifyRevalidateSecret(
  providedSecret: string | null | undefined,
  expectedSecret: string | undefined,
): boolean {
  if (!providedSecret || !expectedSecret) {
    return false;
  }

  const providedHash = createHash("sha256").update(providedSecret).digest();
  const expectedHash = createHash("sha256").update(expectedSecret).digest();

  return timingSafeEqual(providedHash, expectedHash);
}

/** Maksymalna liczba tagów w jednym żądaniu rewalidacji. */
export const MAX_REVALIDATE_TAGS = 100;
/** Maksymalna długość pojedynczego tagu. */
export const MAX_REVALIDATE_TAG_LENGTH = 256;

export type ParsePayloadResult =
  { ok: true; tags: string[] } | { ok: false; error: string };

/**
 * Sprawdza i wyodrębnia listę tagów z treści żądania rewalidacji.
 *
 * Args:
 *     body: Sparsowana treść JSON.
 *
 * Returns:
 *     Obiekt z listą tagów lub błędem walidacji.
 */
export function parseRevalidatePayload(body: unknown): ParsePayloadResult {
  if (body === null || typeof body !== "object" || Array.isArray(body)) {
    return { ok: false, error: "Treść żądania musi być obiektem JSON." };
  }

  const candidate = body as Record<string, unknown>;
  if (!("tags" in candidate) || !Array.isArray(candidate.tags)) {
    return { ok: false, error: "Pole 'tags' musi być tablicą." };
  }

  if (candidate.tags.length === 0) {
    return { ok: false, error: "Tablica 'tags' nie może być pusta." };
  }

  if (candidate.tags.length > MAX_REVALIDATE_TAGS) {
    return {
      ok: false,
      error: `Tablica 'tags' może mieć najwyżej ${MAX_REVALIDATE_TAGS} elementów.`,
    };
  }

  for (const tag of candidate.tags) {
    if (typeof tag === "string" && tag.length > MAX_REVALIDATE_TAG_LENGTH) {
      return {
        ok: false,
        error: `Tag może mieć najwyżej ${MAX_REVALIDATE_TAG_LENGTH} znaków.`,
      };
    }
    if (typeof tag !== "string" || tag.trim().length === 0) {
      return {
        ok: false,
        error: "Każdy element w 'tags' musi być niepustym ciągiem znaków.",
      };
    }
  }

  return { ok: true, tags: candidate.tags as string[] };
}

export type RevalidateTagFunction = (tag: string) => void;

export type HandleRevalidateOptions = {
  secret?: string;
  revalidateTagFn?: RevalidateTagFunction;
};

/**
 * Domyślna funkcja unieważniająca tag w pamięci podręcznej Next.js.
 *
 * Wywołanie spoza Server Action (Route Handler wołany przez backend) nie może
 * użyć `updateTag`, więc `{ expire: 0 }` wygasza wpis natychmiast
 * (profil "max" tylko oznaczałby go jako nieświeży).
 */
export function defaultRevalidateTag(tag: string): void {
  revalidateTag(tag, { expire: 0 });
}

/**
 * Obsługuje żądanie POST /api/revalidate.
 *
 * Weryfikuje sekret autoryzacyjny, parsuje treść i wywołuje unieważnienie
 * dla każdego przekazanego tagu.
 *
 * Args:
 *     request: Żądanie HTTP.
 *     options: Opcjonalne wstrzyknięcie sekretu lub funkcji rewalidacji (testy).
 *
 * Returns:
 *     Odpowiedź HTTP (401, 400 lub 200).
 */
export async function handleRevalidateRequest(
  request: Request,
  options?: HandleRevalidateOptions,
): Promise<Response> {
  const expectedSecret = options?.secret ?? process.env.REVALIDATE_SECRET;
  const providedSecret = request.headers.get(REVALIDATE_SECRET_HEADER);

  if (!verifyRevalidateSecret(providedSecret, expectedSecret)) {
    return Response.json(
      { error: "Brak lub niepoprawny sekret rewalidacji." },
      { status: 401 },
    );
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json(
      { error: "Nieprawidłowy format JSON." },
      { status: 400 },
    );
  }

  const parsed = parseRevalidatePayload(body);
  if (!parsed.ok) {
    return Response.json({ error: parsed.error }, { status: 400 });
  }

  const revalidateFn = options?.revalidateTagFn ?? defaultRevalidateTag;
  for (const tag of parsed.tags) {
    revalidateFn(tag);
  }

  return Response.json({ revalidated: true, tags: parsed.tags });
}
