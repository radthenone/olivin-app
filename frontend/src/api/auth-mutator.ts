import { httpClient } from "@core/http/client";
import type { ApiError } from "@core/http/errors";
import { createAuthMutator } from "./create-auth-mutator";

/**
 * Mutator wymagany przez Orval dla allauth.
 *
 * Dlaczego istnieje:
 * Orval wywołuje `authInstance`, a my pod spodem używamy własnego HttpClienta.
 */
const authMutator = createAuthMutator(httpClient);

export function authInstance<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  return authMutator<T>(url, options);
}

export type ErrorType<Error> = ApiError<Error>;
export type BodyType<BodyData> = BodyData;
