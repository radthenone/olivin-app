/**
 * Root layout — inicjalizuje providery i redirektuje na właściwy ekran.
 * Stan sesji pochodzi z TanStack Query przez endpoint allauth session.
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
import { useAuth } from "@features/auth";

export default function AppLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppNavigator />
    </QueryClientProvider>
  );
}

function AppNavigator() {
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
    <>
      {platformRender({
        web: <>{stack}</>,
        native: (
          <SafeAreaProvider initialMetrics={initialWindowMetrics}>
            <SafeView>{stack}</SafeView>
          </SafeAreaProvider>
        ),
      })}
    </>
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

    const inAuth =
      rootSegment === "(auth)" ||
      rootSegment === "login" ||
      rootSegment === "register" ||
      rootSegment === "verify-email" ||
      rootSegment === "mfa" ||
      rootSegment === "forgot-password";
    const inApp = rootSegment === "(app)" || rootSegment === "home";

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
