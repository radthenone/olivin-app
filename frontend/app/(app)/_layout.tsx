import { Redirect, Stack, usePathname } from "expo-router";
import { useAuthContext } from "@core/auth/auth.provider";
import { useCurrentProfile } from "@features/account/hooks/use-current-profile";
import { isProfileComplete } from "@features/account/services/profile.service";

/**
 * Layout route group dla zalogowanej części aplikacji.
 *
 * Dlaczego istnieje:
 * grupa `(app)` jest chroniona przez root layout i może później dostać
 * własny tab navigator albo stack dla ekranów biznesowych.
 */
export default function AppLayout() {
  const pathname = usePathname();
  const auth = useAuthContext();
  const profile = useCurrentProfile({ enabled: auth.isAuthenticated });
  const shouldCompleteProfile =
    auth.isAuthenticated &&
    profile.isSuccess &&
    !isProfileComplete(profile.data) &&
    pathname !== "/profile-completion";

  if (shouldCompleteProfile) {
    return <Redirect href="/profile-completion" />;
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: "#ffffff" },
      }}
    />
  );
}
