/**
 * Pozostałość kompatybilności po poprzednim kliencie HTTP.
 *
 * Fetch nie ma interceptorów, więc odpowiedzialności auth, CSRF, wersjonowania
 * i logowania są wykonywane jawnie w `client.ts`.
 */
class ApiInterceptorManager {
  setupAll(): Record<string, never> {
    return {};
  }

  ejectAll(): void {
    // Brak interceptorów do odpięcia w fetch client.
  }
}

export const interceptorManager = new ApiInterceptorManager();
