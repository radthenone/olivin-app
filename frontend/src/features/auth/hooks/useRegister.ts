/**
 * useRegister.ts
 *
 * Hook do rejestracji nowego użytkownika z fork-join:
 * → allauth signup + opcjonalny profil + opcjonalny adres.
 */
import { useState } from "react";
import { authService, useAuthStore } from "@core/auth";
import type { RegisterPayload } from "@core/auth";

export interface UseRegisterResult {
  register: (payload: RegisterPayload) => Promise<void>;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
}

export function useRegister(): UseRegisterResult {
  const { setSession } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const register = async (payload: RegisterPayload) => {
    setIsLoading(true);
    setError(null);

    try {
      const session = await authService.register(payload);
      setSession(session);
    } catch (err: unknown) {
      const message = extractRegisterError(err);
      setError(message);
      setSession(null);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    register,
    isLoading,
    error,
    clearError: () => setError(null),
  };
}

function extractRegisterError(err: unknown): string {
  const data = (err as any)?.response?.data;

  if (Array.isArray(data?.errors)) {
    return data.errors
      .map((e: any) => {
        const field = e.param ? `[${e.param}] ` : "";
        return `${field}${e.message ?? e}`;
      })
      .join("\n");
  }

  if (typeof data?.detail === "string") return data.detail;
  if (err instanceof Error) return err.message;

  return "Rejestracja nie powiodła się. Spróbuj ponownie.";
}
