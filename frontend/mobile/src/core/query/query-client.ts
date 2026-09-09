import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "@core/http/errors";

/**
 * Globalny klient TanStack Query.
 *
 * Dlaczego istnieje:
 * TanStack Query jest jedynym źródłem prawdy dla danych z backendu:
 * sesji, profilu, adresów, zamówień itd.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 0,
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        if (failureCount >= 1) return false;
        if (!(error instanceof ApiError)) return false;

        return error.isNetworkError() || error.isServerError();
      },
    },
    mutations: {
      retry: false,
    },
  },
});
