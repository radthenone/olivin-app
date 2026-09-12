import { Redirect } from "expo-router";
import { useAuthContext } from "@core/auth/auth.provider";

/**
 * Wejściowa trasa aplikacji.
 *
 * Dlaczego istnieje:
 * Expo Router potrzebuje index route, a właściwy ekran zależy od sesji.
 */
export default function IndexRoute() {
  const auth = useAuthContext();

  if (auth.isAuthenticated) {
    return <Redirect href="/home" />;
  }

  if (auth.isMfaRequired) {
    return <Redirect href="/mfa" />;
  }

  if (auth.isEmailVerificationRequired) {
    return <Redirect href="/verify-email" />;
  }

  return <Redirect href="/login" />;
}
