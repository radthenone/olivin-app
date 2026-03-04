import { CONFIG } from "src/core/env";

export const ENDPOINTS = {
  AUTH: {
    LOGIN: `/_allauth/${CONFIG.CLIENT}/v1/auth/login/`,
    LOGOUT: `/_allauth/${CONFIG.CLIENT}/v1/auth/logout/`,
    REGISTER: `/_allauth/${CONFIG.CLIENT}/v1/auth/signup/`,
    PASSWORD_RESET: `/_allauth/${CONFIG.CLIENT}/v1/account/password/reset/`,
  },
  // AUTH: {
  //   LOGIN: "/api/auth/login/",
  //   REGISTER: "/api/auth/register/",
  //   LOGOUT: "/api/auth/logout/",
  //   REFRESH: "/api/auth/refresh/",
  //   FORGOT_PASSWORD: "/api/auth/forgot-password/",
  //   VERIFY_2FA: "/api/auth/verify-2fa/",
  // },
  // PRODUCTS: {
  //   LIST: "/api/products/",
  //   DETAIL: (id: string | number) => `/api/products/${id}/`,
  //   SEARCH: "/api/products/search/",
  // },
  // ORDERS: {
  //   LIST: "/api/orders/",
  //   DETAIL: (id: string | number) => `/api/orders/${id}/`,
  //   CREATE: "/api/orders/",
  // },
  // CART: {
  //   GET: "/api/cart/",
  //   ADD_ITEM: "/api/cart/add/",
  //   REMOVE_ITEM: (id: string | number) => `/api/cart/remove/${id}/`,
  //   CLEAR: "/api/cart/clear/",
  // },
  HEALTH: "/health/",
  LOGS: "/logs/",
} as const;
