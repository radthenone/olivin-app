import * as SecureStore from "expo-secure-store";
import { isNative } from "@lib";

const SESSION_TOKEN_KEY = "sessionToken";

export const authStorage = {
  async getSessionToken(): Promise<string | null> {
    if (isNative) {
      return SecureStore.getItemAsync(SESSION_TOKEN_KEY);
    }
    return null;
  },

  async setSessionToken(token: string): Promise<void> {
    if (isNative) {
      await SecureStore.setItemAsync(SESSION_TOKEN_KEY, token);
    }
  },

  async removeSessionToken(): Promise<void> {
    if (isNative) {
      await SecureStore.deleteItemAsync(SESSION_TOKEN_KEY);
    }
  },
};
