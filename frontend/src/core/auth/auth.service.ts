import {
  postAllauthClientV1AuthLogin,
  postAllauthClientV1AuthSignup,
} from "@api/generated/auth/authentication-account/authentication-account";
import { postAllauthClientV1Auth2faAuthenticate } from "@api/generated/auth/authentication-2fa/authentication-2fa";
import {
  getAllauthClientV1AuthSession,
  deleteAllauthClientV1AuthSession,
} from "@api/generated/auth/authentication-current-session/authentication-current-session";
import type { LoginBody, SignupBody } from "@api/generated/auth/schemas";
import { authStorage } from "./auth.storage";
import type { AllauthClient, AuthFlow } from "./auth.types";
import { CONFIG } from "@core/env";

async function persistSessionToken(meta: unknown) {
  const token = (meta as any)?.session_token;
  if (typeof token === "string") {
    await authStorage.setSessionToken(token);
  }
}

function extractFlows(data: unknown): AuthFlow[] {
  return ((data as any)?.flows as AuthFlow[] | undefined) ?? [];
}

async function handleAxiosError(error: unknown): Promise<AuthFlow[]> {
  const response = (error as any)?.response;
  const status: number = response?.status;
  const data = response?.data;

  if (status === 401) {
    await persistSessionToken(data?.meta);
    return extractFlows(data?.data);
  }

  if (status === 410) {
    await authStorage.removeSessionToken();
    throw new Error("SESSION_EXPIRED");
  }

  throw error;
}

export async function login(
  credentials: LoginBody,
  client: AllauthClient = CONFIG.CLIENT,
): Promise<AuthFlow[] | null> {
  try {
    const res = await postAllauthClientV1AuthLogin(client, credentials);
    await persistSessionToken((res as any)?.meta);
    return null;
  } catch (error) {
    return handleAxiosError(error);
  }
}

export async function signup(
  data: SignupBody,
  client: AllauthClient = CONFIG.CLIENT,
): Promise<AuthFlow[] | null> {
  try {
    const res = await postAllauthClientV1AuthSignup(client, data);
    await persistSessionToken((res as any)?.meta);
    return null;
  } catch (error) {
    return handleAxiosError(error);
  }
}

export async function logout(
  client: AllauthClient = CONFIG.CLIENT,
): Promise<void> {
  try {
    await deleteAllauthClientV1AuthSession(client);
  } finally {
    await authStorage.removeSessionToken();
  }
}

export async function verifyMfa(
  code: string,
  client: AllauthClient = CONFIG.CLIENT,
): Promise<AuthFlow[] | null> {
  try {
    const res = await postAllauthClientV1Auth2faAuthenticate(client, { code });
    await persistSessionToken((res as any)?.meta);
    return null;
  } catch (error) {
    return handleAxiosError(error);
  }
}

export async function getSession(
  client: AllauthClient = CONFIG.CLIENT,
): Promise<{
  isAuthenticated: boolean;
  flows: AuthFlow[];
}> {
  try {
    const res = await getAllauthClientV1AuthSession(client);
    await persistSessionToken((res as any)?.meta);
    return {
      isAuthenticated: (res as any)?.meta?.is_authenticated === true,
      flows: extractFlows((res as any)?.data),
    };
  } catch (error) {
    const response = (error as any)?.response;
    if (response?.status === 410) {
      await authStorage.removeSessionToken();
      throw new Error("SESSION_EXPIRED");
    }
    if (response?.status === 401) {
      await persistSessionToken(response?.data?.meta);
      return {
        isAuthenticated: false,
        flows: extractFlows(response?.data?.data),
      };
    }
    throw error;
  }
}
