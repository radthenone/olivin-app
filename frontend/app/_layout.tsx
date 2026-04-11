/**
 * Root layout — inicjalizuje sesję i redirektuje na właściwy ekran.
 * useSessionInit() sprawdza stan sesji JEDNORAZOWO przy starcie.
 */
import "../styles/global.css";
import { Stack, useRouter, useSegments } from "expo-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { useEffect } from "react";
import { queryClient } from "@lib/queryClient";
import {
  SafeAreaProvider,
  initialWindowMetrics,
} from "react-native-safe-area-context";
import { platformRender } from "@lib";
import { SafeView } from "@ui";
import { useSessionInit, useAuth } from "@features/auth";

export default function AppLayout() {
  useSessionInit();
  useAuthGuard();

  const stack = (
    <Stack initialRouteName="index">
      <Stack.Screen name="index" options={{ headerShown: false }} />
      <Stack.Screen name="(auth)" options={{ headerShown: false }} />
      <Stack.Screen name="(app)" options={{ headerShown: false }} />
      <Stack.Screen
        name="+not-found"
        options={{ title: "Not Found", headerShown: false }}
      />
    </Stack>
  );

  return (
    <QueryClientProvider client={queryClient}>
      {platformRender({
        web: <>{stack}</>,
        native: (
          <SafeAreaProvider initialMetrics={initialWindowMetrics}>
            <SafeView>{stack}</SafeView>
          </SafeAreaProvider>
        ),
      })}
    </QueryClientProvider>
  );
}

/**
 * Guard nawigacji — na podstawie `session.meta.is_authenticated` oraz flows
 * przenosi użytkownika do właściwej grupy routów.
 */
function useAuthGuard() {
  const router = useRouter();
  const segments = useSegments();
  const rootSegment = segments[0];
  const {
    session,
    isSessionChecked,
    isAuthenticated,
    isPendingMfa,
    isPendingVerification,
  } = useAuth();

  useEffect(() => {
    if (!isSessionChecked) return; // czekamy na sprawdzenie sesji

    const inAuth = rootSegment === "(auth)";
    const inApp = rootSegment === "(app)";

    if (isPendingMfa && !inAuth) {
      router.replace("/(auth)/mfa");
    } else if (isPendingVerification && !inAuth) {
      router.replace("/(auth)/verify-email");
    } else if (isAuthenticated && inAuth) {
      router.replace("/(app)/home");
    } else if (!isAuthenticated && inApp) {
      router.replace("/(auth)/login");
    } else if (!isAuthenticated && !inAuth) {
      router.replace("/(auth)/login");
    }
  }, [
    router,
    rootSegment,
    isSessionChecked,
    isAuthenticated,
    isPendingMfa,
    isPendingVerification,
    session,
  ]);
}
