import * as SecureStore from "expo-secure-store";
import { ENV } from "@config/env";
import { log } from "@core/logger";

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/**
 * Przechowuje token sesji allauth dla klienta `app`.
 *
 * Dlaczego istnieje:
 * native nie korzysta z cookie `sessionid`, więc po loginie musi zapisać
 * `meta.session_token` i wysyłać go potem jako `X-Session-Token`.
 */
export const sessionTokenStorage = {
  async get(): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(ENV.SESSION_TOKEN_KEY);
    } catch (error: unknown) {
      log.error("Nie udało się odczytać tokena sesji.", {
        error: getErrorMessage(error),
      });
      return null;
    }
  },

  async set(value: string): Promise<void> {
    try {
      await SecureStore.setItemAsync(ENV.SESSION_TOKEN_KEY, value);
    } catch (error: unknown) {
      log.error("Nie udało się zapisać tokena sesji.", {
        error: getErrorMessage(error),
      });
    }
  },

  async remove(): Promise<void> {
    try {
      await SecureStore.deleteItemAsync(ENV.SESSION_TOKEN_KEY);
    } catch (error: unknown) {
      log.error("Nie udało się usunąć tokena sesji.", {
        error: getErrorMessage(error),
      });
    }
  },
};
