"use client";

import { useState, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { configureWebApi } from "@/lib/api-transport";

// Transport musi być podłączony, zanim którykolwiek komponent wykona żądanie —
// stąd wywołanie w module, a nie w efekcie.
configureWebApi();

export function Providers({ children }: { children: ReactNode }) {
  // Klient zapytań tworzony w stanie, a nie w module: w renderowaniu po stronie
  // serwera moduł jest współdzielony między żądaniami różnych użytkowników, więc
  // wspólny cache przeciekałby dane między nimi.
  const [queryClient] = useState(() => new QueryClient());

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
