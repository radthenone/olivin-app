/**
 * Centralna mapa tras aplikacji.
 *
 * Dlaczego istnieje:
 * unikamy stringów typu "/login" porozrzucanych po kodzie.
 */
export const routes = {
  index: "/",
  login: "/login",
  register: "/register",
  verifyEmail: "/verify-email",
  mfa: "/mfa",
  home: "/home",
  profile: "/profile",
  addresses: "/addresses",
  cart: "/cart",
  settings: "/settings",
  products: "/products",
  productDetail: (slug: string) => `/products/${slug}` as const,
} as const;
