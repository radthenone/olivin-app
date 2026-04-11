import { authStorage } from "./auth.storage";
import { CONFIG } from "@core/env";
import { isNative } from "@lib";

export const authSessionManager = {
  async get(): Promise<{ sessionToken: string } | null> {
    if (!isNative) return null;
    const token = await authStorage.getSessionToken();
    if (!token) return null;
    return { sessionToken: token };
  },

  async set(value: string): Promise<void> {
    if (isNative) {
      await authStorage.setSessionToken(value);
    }
  },

  async remove(): Promise<void> {
    if (isNative) {
      await authStorage.removeSessionToken();
    }
  },
};
