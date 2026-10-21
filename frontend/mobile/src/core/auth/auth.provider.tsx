import { createContext, useContext, type PropsWithChildren } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth, useLogin, useLogout } from "@olivin/features/auth";
import { accountQueryKeys } from "@features/account/constants/account-query-keys";

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
  const queryClient = useQueryClient();
  const auth = useAuth();
  const login = useLogin();
  // Cache konta zostaje w mobile (plasterek konta, ADR 0033), więc to
  // aplikacja dokłada swoje sprzątanie do wspólnego wylogowania.
  const logout = useLogout({
    onLogout: () => {
      queryClient.removeQueries({ queryKey: accountQueryKeys.all });
    },
  });

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
