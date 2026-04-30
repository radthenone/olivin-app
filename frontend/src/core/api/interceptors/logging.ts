/**
 * Logowanie requestów fetch jest wykonywane w `@http/client`.
 */
export function setupLoggingInterceptor(): {
  request: number;
  response: number;
} {
  return { request: -1, response: -1 };
}
