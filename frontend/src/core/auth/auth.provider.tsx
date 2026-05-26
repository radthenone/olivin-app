import { createContext, useContext, type PropsWithChildren } from "react";
import { useAuth } from "@features/auth/hooks/use-auth";
import { useLogin } from "@features/auth/hooks/use-login";
import { useLogout } from "@features/auth/hooks/use-logout";

type AuthContextValue = ReturnType<typeof useAuth> & {
  login: ReturnType<typeof useLogin>;
  logout: ReturnType<typeof useLogout>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Udostępnia stan sesji i akcje auth całej aplikacji.
 *
 * Dlaczego istnieje:
 * Expo Router potrzebuje prostych flag do ochrony route group,
 * a źródłem prawdy nadal pozostaje endpoint allauth `auth/session`.
 */
export function AuthProvider({ children }: PropsWithChildren) {
  const auth = useAuth();
  const login = useLogin();
  const logout = useLogout();

  return (
    <AuthContext.Provider value={{ ...auth, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Zwraca stan auth dostępny w providerze.
 *
 * Dlaczego istnieje:
 * layouty i ekrany nie powinny ponownie składać hooków auth ani znać
 * szczegółów TanStack Query.
 */
export function useAuthContext() {
  const value = useContext(AuthContext);

  if (!value) {
    throw new Error("useAuthContext musi być użyty wewnątrz AuthProvider.");
  }

  return value;
}
