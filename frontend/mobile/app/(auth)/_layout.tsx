import { Stack } from "expo-router";
import { useAuthContext } from "@core/auth/auth.provider";

/**
 * Layout route group dla ekranów auth.
 *
 * Dlaczego istnieje:
 * root layout wpuszcza tu stany niepełnej autoryzacji, a ten layout
 * pilnuje, żeby użytkownik widział tylko właściwy krok flow.
 */
export default function AuthLayout() {
  const auth = useAuthContext();
  const canUsePrimaryAuth =
    auth.isUnauthenticated ||
    (!auth.isMfaRequired && !auth.isEmailVerificationRequired);
  const canVerifyEmail =
    auth.isUnauthenticated || auth.isEmailVerificationRequired;

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: "#ffffff" },
      }}
    >
      <Stack.Protected guard={canUsePrimaryAuth}>
        <Stack.Screen name="login" />
        <Stack.Screen name="login-code" />
        <Stack.Screen name="register" />
        <Stack.Screen name="forgot-password" />
        <Stack.Screen name="reset-password/[key]" />
      </Stack.Protected>

      <Stack.Protected guard={auth.isMfaRequired}>
        <Stack.Screen name="mfa" />
      </Stack.Protected>

      <Stack.Protected guard={canVerifyEmail}>
        <Stack.Screen name="verify-email" />
      </Stack.Protected>
    </Stack>
  );
}
