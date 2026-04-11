/**
 * useLogin.ts
 *
 * Hook do logowania użytkownika.
 * Używa authService.login + aktualizuje authStore.
 */
import { useState } from "react";
import { authService, useAuthStore } from "@core/auth";
import type { LoginCredentials } from "@core/auth";

export interface UseLoginResult {
  login: (credentials: LoginCredentials) => Promise<void>;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
}

export function useLogin(): UseLoginResult {
  const { setSession } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);

    try {
      const session = await authService.login({
        email: credentials.email,
        password: credentials.password,
      });

      setSession(session);
    } catch (err: unknown) {
      const message = extractErrorMessage(err);
      setError(message);
      setSession(null);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    login,
    isLoading,
    error,
    clearError: () => setError(null),
  };
}

function extractErrorMessage(err: unknown): string {
  const data = (err as any)?.response?.data;

  // allauth zwraca errors jako tablicę
  if (Array.isArray(data?.errors)) {
    return data.errors.map((e: any) => e.message ?? e).join(", ");
  }
  if (typeof data?.detail === "string") return data.detail;
  if (err instanceof Error) return err.message;

  return "Błąd logowania. Spróbuj ponownie.";
}
