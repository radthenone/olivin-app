import { allauthClient } from "@core/config/platform";
import {
  getAllauthClientV1AuthSession,
  deleteAllauthClientV1AuthSession,
} from "@api/generated/auth/authentication-current-session/authentication-current-session";
import {
  postAllauthClientV1AuthLogin,
  postAllauthClientV1AuthSignup,
  postAllauthClientV1AuthEmailVerify,
} from "@api/generated/auth/authentication-account/authentication-account";
import { postAllauthClientV1Auth2faAuthenticate } from "@api/generated/auth/authentication-2fa/authentication-2fa";
import {
  postAllauthClientV1AuthPasswordRequest,
  postAllauthClientV1AuthPasswordReset,
} from "@api/generated/auth/authentication-password-reset/authentication-password-reset";
import {
  postAllauthClientV1AuthCodeRequest,
  postAllauthClientV1AuthCodeConfirm,
} from "@api/generated/auth/authentication-login-by-code/authentication-login-by-code";
import { postAllauthClientV1AuthProviderToken } from "@api/generated/auth/authentication-providers/authentication-providers";
import { mapAllauthBodyToAuthState } from "./auth.mapper";

type SocialProviderTokenInput =
  | {
      provider: "google";
      clientId: string;
      idToken: string;
    }
  | {
      provider: "facebook";
      clientId: string;
      accessToken: string;
    };

type AuthResponseLike = {
  status: number;
  data: unknown;
};

function ensureExpectedStatus(
  response: AuthResponseLike,
  expectedStatuses: number[],
  message: string,
) {
  if (!expectedStatuses.includes(response.status)) {
    throw new Error(message);
  }
}

/**
 * Orkiestruje przypadki użycia auth.
 *
 * Dlaczego istnieje:
 * feature hooks nie powinny importować Orvala bezpośrednio
 * ani znać szczegółów odpowiedzi allauth.
 */
export const authService = {
  async getSession() {
    const response = await getAllauthClientV1AuthSession(allauthClient);
    return mapAllauthBodyToAuthState(response.data);
  },

  async login(data: { email: string; password: string }) {
    const response = await postAllauthClientV1AuthLogin(allauthClient, data);
    ensureExpectedStatus(response, [200, 401], "Nie udało się zalogować.");
    return mapAllauthBodyToAuthState(response.data);
  },

  async signup(data: {
    email: string;
    password: string;
    firstName: string;
    lastName: string;
    dateOfBirth: string;
    phoneNumber: string;
  }) {
    const response = await postAllauthClientV1AuthSignup(allauthClient, data);
    ensureExpectedStatus(response, [200, 401], "Nie udało się utworzyć konta.");
    return mapAllauthBodyToAuthState(response.data);
  },

  async verifyEmail(data: { key: string }) {
    const response = await postAllauthClientV1AuthEmailVerify(
      allauthClient,
      data,
    );
    ensureExpectedStatus(
      response,
      [200, 401],
      "Nie udało się potwierdzić emaila.",
    );
    return mapAllauthBodyToAuthState(response.data);
  },

  async requestPasswordReset(data: { email: string }) {
    const response = await postAllauthClientV1AuthPasswordRequest(
      allauthClient,
      data,
    );
    ensureExpectedStatus(
      response,
      [200, 401],
      "Nie udało się wysłać resetu hasła.",
    );
    return response.data;
  },

  async resetPassword(data: { key: string; password: string }) {
    const response = await postAllauthClientV1AuthPasswordReset(
      allauthClient,
      data,
    );
    ensureExpectedStatus(response, [200, 401], "Nie udało się ustawić hasła.");
    return mapAllauthBodyToAuthState(response.data);
  },

  async authenticateMfa(data: { code: string }) {
    const response = await postAllauthClientV1Auth2faAuthenticate(
      allauthClient,
      data,
    );
    ensureExpectedStatus(
      response,
      [200, 401],
      "Nie udało się potwierdzić MFA.",
    );
    return mapAllauthBodyToAuthState(response.data);
  },

  async requestLoginCode(data: { email: string }) {
    const response = await postAllauthClientV1AuthCodeRequest(
      allauthClient,
      data,
    );
    ensureExpectedStatus(
      response,
      [200, 401],
      "Nie udało się wysłać kodu logowania.",
    );
    return response.data;
  },

  async confirmLoginCode(data: { code: string }) {
    const response = await postAllauthClientV1AuthCodeConfirm(
      allauthClient,
      data,
    );
    ensureExpectedStatus(
      response,
      [200, 401],
      "Nie udało się potwierdzić kodu logowania.",
    );
    return mapAllauthBodyToAuthState(response.data);
  },

  async loginWithProviderToken(data: SocialProviderTokenInput) {
    const token =
      data.provider === "google"
        ? { client_id: data.clientId, id_token: data.idToken }
        : { client_id: data.clientId, access_token: data.accessToken };

    const response = await postAllauthClientV1AuthProviderToken(allauthClient, {
      provider: data.provider,
      process: "login",
      token,
    });

    ensureExpectedStatus(
      response,
      [200, 401],
      "Nie udało się zalogować social.",
    );
    return mapAllauthBodyToAuthState(response.data);
  },

  async logout() {
    await deleteAllauthClientV1AuthSession(allauthClient);
  },
};
