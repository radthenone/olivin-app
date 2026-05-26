import { useState } from "react";
import { Text } from "react-native";
import { ErrorMessage } from "@ui/feedback/ErrorMessage";
import { Button } from "@ui/primitives/Button";
import { TextField } from "@ui/primitives/TextField";
import { useLogin } from "../hooks/use-login";
import { loginSchema } from "../forms/login.schema";
import { Link } from "expo-router";
import { AuthShell } from "../components/AuthShell";
import { useSocialLogin } from "../hooks/use-social-login";

/**
 * Ekran logowania.
 *
 * Dlaczego istnieje:
 * jest pierwszym wzorcowym vertical slice: UI -> hook -> service -> Orval
 * -> mutator -> HttpClient -> backend allauth.
 */
export function LoginScreen() {
  const login = useLogin();
  const socialLogin = useSocialLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  function handleSubmit() {
    const parsed = loginSchema.safeParse({ email, password });

    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Sprawdź dane.");
      return;
    }

    setFormError(null);
    login.mutate(parsed.data);
  }

  return (
    <AuthShell
      title="Zaloguj się"
      subtitle="Wejdź do konta Olivin, żeby zarządzać profilem, bezpieczeństwem i zamówieniami."
      footer={
        <>
          <Link href="/login-code">
            <Text className="text-center text-sm font-medium text-neutral-700 underline">
              Zaloguj się kodem email
            </Text>
          </Link>
          <Link href="/forgot-password">
            <Text className="text-center text-sm font-medium text-neutral-700 underline">
              Nie pamiętasz hasła?
            </Text>
          </Link>
          <Link href="/register">
            <Text className="text-center text-base text-neutral-950 underline">
              Nie masz konta? Zarejestruj się
            </Text>
          </Link>
        </>
      }
    >
      <TextField
        autoCapitalize="none"
        autoComplete="email"
        editable={!login.isPending}
        keyboardType="email-address"
        label="Email"
        onChangeText={(value) => {
          setEmail(value);
          setFormError(null);
        }}
        placeholder="email@example.com"
        returnKeyType="next"
        value={email}
      />

      <TextField
        autoComplete="current-password"
        editable={!login.isPending}
        label="Hasło"
        onChangeText={(value) => {
          setPassword(value);
          setFormError(null);
        }}
        onSubmitEditing={handleSubmit}
        placeholder="Hasło"
        returnKeyType="done"
        secureTextEntry
        value={password}
      />

      <ErrorMessage
        message={
          formError ??
          socialLogin.errorMessage ??
          (login.isError ? "Nie udało się zalogować." : null)
        }
      />

      <Button disabled={login.isPending} onPress={handleSubmit}>
        {login.isPending ? "Logowanie..." : "Zaloguj"}
      </Button>

      <Button
        disabled={
          login.isPending || socialLogin.isPending || !socialLogin.isGoogleReady
        }
        onPress={socialLogin.startGoogleLogin}
        variant="outline"
      >
        Kontynuuj z Google
      </Button>

      <Button
        disabled={
          login.isPending ||
          socialLogin.isPending ||
          !socialLogin.isFacebookReady
        }
        onPress={socialLogin.startFacebookLogin}
        variant="outline"
      >
        Kontynuuj z Facebookiem
      </Button>
    </AuthShell>
  );
}
