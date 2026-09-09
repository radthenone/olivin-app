import { ENV } from "@config/env";
import { allauthClient } from "@config/platform";

const BASE_URL = ENV.API_BASE_URL;
const ALLAUTH_PREFIX = `_allauth/${allauthClient}/v1`;
const ALLAUTH_URL = `${BASE_URL}/${ALLAUTH_PREFIX}`;

export const ENDPOINTS = Object.freeze({
  ALLAUTH: {
    SESSION: `${ALLAUTH_URL}/auth/session/`,
    LOGIN: `${ALLAUTH_URL}/auth/login/`,
    LOGOUT: `${ALLAUTH_URL}/auth/logout/`,
  },
  APPS: {},
  HEALTH: `${BASE_URL}/health/`,
});
