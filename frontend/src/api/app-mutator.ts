import { httpClient } from "@core/http/client";
import type { ApiError } from "@core/http/errors";
import { createAppMutator } from "./create-app-mutator";

/**
 * Mutator wymagany przez Orval dla endpointów aplikacyjnych.
 *
 * Dlaczego istnieje:
 * Orval generuje funkcje endpointów, ale transport należy do naszej aplikacji.
 */
const appMutator = createAppMutator(httpClient);

export function appInstance<T>(url: string, options?: RequestInit): Promise<T> {
  return appMutator<T>(url, options);
}

export type ErrorType<Error> = ApiError<Error>;
export type BodyType<BodyData> = BodyData;
