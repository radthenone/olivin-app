type AuthHttpResponse = {
  status: number;
  data: unknown;
};

type AllauthError = {
  message?: unknown;
};

/**
 * Błąd odpowiedzi allauth z zachowanym ciałem.
 *
 * Dzięki temu formularz webowy może dalej przypisać błędy do pól, a mobile
 * dostaje zwykły `error.message` do wyświetlenia.
 */
export class AuthResponseError extends Error {
  readonly response: AuthHttpResponse;

  constructor(response: AuthHttpResponse, message: string) {
    super(message);
    this.name = "AuthResponseError";
    this.response = response;
  }
}

/**
 * Komunikaty walidacji allauth (`errors[].message` z 400), np. brak zgody
 * albo zajęty email — czytelniejsze niż ogólny błąd formularza.
 */
export function allauthErrorMessage(data: unknown): string | null {
  const errors = (data as { errors?: unknown } | null)?.errors;
  if (!Array.isArray(errors)) return null;

  const messages = (errors as AllauthError[])
    .map((error) => error.message)
    .filter((text): text is string => typeof text === "string");

  return messages.length > 0 ? messages.join("\n") : null;
}

/**
 * Przepuszcza statusy, które są częścią protokołu sesji, a resztę zamienia na
 * błąd z komunikatem backendu. Dzięki temu formularze dostają `isError`
 * i `error.message` zamiast cicho ignorować odrzuconą odpowiedź.
 */
export function requireAuthStatus<TResponse extends AuthHttpResponse>(
  response: TResponse,
  expectedStatuses: number[],
  fallbackMessage: string,
): TResponse {
  if (!expectedStatuses.includes(response.status)) {
    throw new AuthResponseError(
      response,
      allauthErrorMessage(response.data) ?? fallbackMessage,
    );
  }

  return response;
}
