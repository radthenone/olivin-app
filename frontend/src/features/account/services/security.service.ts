import { allauthClient } from "@core/config/platform";
import {
  deleteAllauthClientV1AccountAuthenticatorsTotp,
  getAllauthClientV1AccountAuthenticatorsTotp,
  postAllauthClientV1AccountAuthenticatorsTotp,
} from "@api/generated/auth/account-2fa/account-2fa";
import { postAllauthClientV1AccountPasswordChange } from "@api/generated/auth/account-password/account-password";
import { postAllauthClientV1AccountEmail } from "@api/generated/auth/account-email/account-email";

type AuthResponseLike = {
  status: number;
  data?: unknown;
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
 * Serwis ustawień bezpieczeństwa konta.
 *
 * Dlaczego istnieje:
 * ekran ustawień konta nie powinien znać nazw endpointów allauth ani
 * rozróżnienia `browser`/`app` dla web/native.
 */
export const securityService = {
  async getTotpAuthenticator() {
    const response =
      await getAllauthClientV1AccountAuthenticatorsTotp(allauthClient);

    if (response.status === 200) {
      return {
        status: "active" as const,
        authenticator: response.data.data,
        setup: null,
      };
    }

    if (response.status === 404) {
      return {
        status: "inactive" as const,
        authenticator: null,
        setup: response.data.meta,
      };
    }

    return {
      status: "unavailable" as const,
      authenticator: null,
      setup: null,
    };
  },

  async activateTotp(data: { code: string }) {
    const response = await postAllauthClientV1AccountAuthenticatorsTotp(
      allauthClient,
      data,
    );
    ensureExpectedStatus(response, [200], "Nie udało się włączyć MFA.");
    return response.data;
  },

  async deactivateTotp() {
    const response =
      await deleteAllauthClientV1AccountAuthenticatorsTotp(allauthClient);
    ensureExpectedStatus(response, [200], "Nie udało się wyłączyć MFA.");
    return response.data;
  },

  async changePassword(data: {
    currentPassword?: string;
    newPassword: string;
  }) {
    const response = await postAllauthClientV1AccountPasswordChange(
      allauthClient,
      {
        current_password: data.currentPassword || undefined,
        new_password: data.newPassword,
      },
    );
    ensureExpectedStatus(response, [200], "Nie udało się zmienić hasła.");
    return response.data;
  },

  async requestEmailChange(data: { email: string }) {
    const response = await postAllauthClientV1AccountEmail(allauthClient, data);
    ensureExpectedStatus(
      response,
      [200],
      "Nie udało się rozpocząć zmiany emaila.",
    );
    return response.data;
  },
};
