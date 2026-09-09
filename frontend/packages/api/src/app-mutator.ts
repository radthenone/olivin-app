import type { ApiError } from "./errors";
import { appFetch } from "./transport";

/**
 * Mutator wymagany przez Orval dla endpointów domenowych.
 *
 * Nie zawiera żadnej logiki transportu — deleguje do implementacji wstrzykniętej
 * przez aplikację, żeby pakiet pozostał wolny od wiedzy o platformie.
 */
export function appInstance<TData>(
  url: string,
  options?: RequestInit,
): Promise<TData> {
  return appFetch<TData>(url, options);
}

export type ErrorType<TError> = ApiError<TError>;
export type BodyType<TBody> = TBody;
