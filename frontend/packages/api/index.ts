// Publiczna powierzchnia pakietu.
//
// Wygenerowany klient jest importowany ścieżką (np. @olivin/api/generated/...),
// bo jest go zbyt dużo, żeby re-eksportować wszystko bez psucia tree-shakingu.
// Tutaj wychodzi tylko to, co aplikacja musi znać, żeby pakiet zadziałał.

export {
  configureApi,
  resetApi,
  type ApiFetcher,
  type ApiTransport,
} from "./src/transport";

export { ApiError, type ApiErrorResponse } from "./src/errors";

export type {
  HttpMethod,
  HttpRequest,
  HttpRequestConfig,
  HttpResponse,
  Primitive,
  QueryParams,
  TimeoutController,
} from "./src/types";
