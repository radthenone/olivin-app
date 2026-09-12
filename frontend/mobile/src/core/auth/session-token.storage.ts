/**
 * Fallback dla platform bez dedykowanej implementacji.
 *
 * Dlaczego istnieje:
 * Expo wybiera `session-token.storage.native.ts` albo
 * `session-token.storage.web.ts`. Ten plik zostaje jako bezpieczny fallback.
 */
export const sessionTokenStorage = {
  async get(): Promise<string | null> {
    return null;
  },

  async set(_value: string): Promise<void> {},

  async remove(): Promise<void> {},
};
