/**
 * auth.storage.ts
 *
 * Abstrakcja przechowywania session tokena.
 * - Native (Android/iOS): expo-secure-store (zaszyfrowany)
 * - Web:  sessionStorage (token żyje tylko w tej karcie; cookie sesji
 *         obsługuje Django po stronie serwera, więc nie potrzebujemy
 *         długotrwałego przechowywania tokena na webbie)
 */
import * as SecureStore from "expo-secure-store";
import { isNative } from "@lib";
import { CONFIG } from "@core/env";

export const authStorage = {
  async getSessionToken(): Promise<string | null> {
    if (isNative) {
      return SecureStore.getItemAsync(CONFIG.SESSION_TOKEN_KEY);
    }
    return null;
  },

  async setSessionToken(
    value: string,
    options?: SecureStore.SecureStoreOptions | undefined,
  ): Promise<void> {
    if (isNative) {
      await SecureStore.setItemAsync(CONFIG.SESSION_TOKEN_KEY, value, options);
    }
  },

  async removeSessionToken(
    options?: SecureStore.SecureStoreOptions | undefined,
  ): Promise<void> {
    if (isNative) {
      await SecureStore.deleteItemAsync(CONFIG.SESSION_TOKEN_KEY, options);
    }
  },
};
