import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // dane świeże przez 5 minut
      retry: 2, // 2 próby przy błędzie
      refetchOnWindowFocus: true, // odśwież gdy user wraca do zakładki
    },
  },
});
