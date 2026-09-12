/**
 * Webowy adapter tokena sesji allauth.
 *
 * Dlaczego istnieje:
 * web używa cookie `sessionid` i `csrftoken`, więc nie zapisujemy
 * `meta.session_token`. Plik utrzymuje ten sam import co native.
 */
export const sessionTokenStorage = {
  async get(): Promise<string | null> {
    return null;
  },

  async set(_value: string): Promise<void> {},

  async remove(): Promise<void> {},
};
