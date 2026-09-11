import type { ApiError } from "./errors";
import { authFetch } from "./transport";

/**
 * Mutator wymagany przez Orval dla endpointów sesji allauth.
 *
 * Osobny od mutatora domenowego, bo to dwa niezależne schematy o różnym cyklu
 * życia: schemat allauth pochodzi z biblioteki, domenowy z naszego kodu.
 */
export function authInstance<TData>(
  url: string,
  options?: RequestInit,
): Promise<TData> {
  return authFetch<TData>(url, options);
}

export type ErrorType<TError> = ApiError<TError>;
export type BodyType<TBody> = TBody;
