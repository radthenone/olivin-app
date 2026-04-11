/**
 * usePasswordReset.ts
 *
 * Hook do obsługi całego flow resetu hasła:
 * 1. request — wysyła e-mail z linkiem/kodem
 * 2. confirm — ustawia nowe hasło na podstawie klucza z e-maila
 */
import { useState } from "react";
import { authService, useAuthStore } from "@core/auth";
import type {
  RequestPasswordResetPayload,
  ConfirmPasswordResetPayload,
} from "@core/auth";

export interface UsePasswordResetResult {
  requestReset: (payload: RequestPasswordResetPayload) => Promise<void>;
  confirmReset: (payload: ConfirmPasswordResetPayload) => Promise<void>;
  isLoading: boolean;
  isSuccess: boolean;
  error: string | null;
  clearError: () => void;
  reset: () => void;
}

export function usePasswordReset(): UsePasswordResetResult {
  const { setSession } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const requestReset = async (payload: RequestPasswordResetPayload) => {
    setIsLoading(true);
    setError(null);
    setIsSuccess(false);
    try {
      await authService.requestPasswordReset(payload);
      setIsSuccess(true);
    } catch (err) {
      setError(
        extractError(err, "Nie udało się wysłać e-maila. Spróbuj ponownie."),
      );
    } finally {
      setIsLoading(false);
    }
  };

  const confirmReset = async (payload: ConfirmPasswordResetPayload) => {
    setIsLoading(true);
    setError(null);
    try {
      const session = await authService.confirmPasswordReset(payload);
      setSession(session);
      setIsSuccess(true);
    } catch (err) {
      setError(
        extractError(err, "Nieprawidłowy lub wygasły link resetu hasła."),
      );
    } finally {
      setIsLoading(false);
    }
  };

  return {
    requestReset,
    confirmReset,
    isLoading,
    isSuccess,
    error,
    clearError: () => setError(null),
    reset: () => {
      setIsSuccess(false);
      setError(null);
    },
  };
}

function extractError(err: unknown, fallback: string): string {
  const data = (err as any)?.response?.data;
  if (Array.isArray(data?.errors)) {
    return data.errors.map((e: any) => e.message ?? e).join(", ");
  }
  if (typeof data?.detail === "string") return data.detail;
  if (err instanceof Error) return err.message;
  return fallback;
}
