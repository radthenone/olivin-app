import type { HttpResponse } from "@olivin/api";
import { ApiError } from "@olivin/api";

/**
 * Klient HTTP aplikacji webowej.
 *
 * Odpowiednik klienta mobilnego, ale z innym nośnikiem sesji: allauth w trybie
 * przeglądarkowym trzyma sesję w ciasteczkach, więc żądania idą z
 * `credentials: "include"`, a nie z nagłówkiem tokenu.
 *
 * Kształt odpowiedzi jest celowo taki sam jak po stronie mobilnej, bo obie
 * aplikacje konsumują ten sam wygenerowany klient.
 */

function baseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_BACKEND_URL;

  if (!configured) {
    throw new Error(
      "Brak NEXT_PUBLIC_BACKEND_URL. Bez adresu backendu aplikacja webowa nie " +
        "ma dokąd wysłać żądania.",
    );
  }

  return configured.replace(/\/$/, "");
}

function resolve(url: string): string {
  return url.startsWith("http") ? url : `${baseUrl()}${url}`;
}

async function readBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  const text = await response.text();
  return text.length > 0 ? text : undefined;
}

export async function webRequest<TData>(
  url: string,
  options: RequestInit = {},
  { acceptAllStatuses = false }: { acceptAllStatuses?: boolean } = {},
): Promise<HttpResponse<TData>> {
  const target = resolve(url);

  let response: Response;

  try {
    response = await fetch(target, {
      ...options,
      credentials: "include",
      headers: {
        accept: "application/json",
        "content-type": "application/json",
        ...options.headers,
      },
    });
  } catch (error: unknown) {
    // Brak odpowiedzi to nie jest status HTTP — status 0 odróżnia awarię sieci
    // od odpowiedzi serwera, tak samo jak po stronie mobilnej.
    throw new ApiError(
      {
        status: 0,
        data: undefined,
        headers: new Headers(),
        config: { url: target },
      },
      error instanceof Error
        ? error.message
        : "Żądanie sieciowe nie powiodło się",
    );
  }

  const data = (await readBody(response)) as TData;

  if (!response.ok && !acceptAllStatuses) {
    throw new ApiError(
      {
        status: response.status,
        data,
        headers: response.headers,
        config: { url: target },
      },
      `Żądanie zakończone statusem ${response.status}`,
    );
  }

  return { data, status: response.status, headers: response.headers };
}
