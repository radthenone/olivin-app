import { useState } from "react";
import { Text } from "react-native";
import { Link } from "expo-router";
import { ErrorMessage } from "@ui/feedback/ErrorMessage";
import { Button } from "@ui/primitives/Button";
import { TextField } from "@ui/primitives/TextField";
import { AuthShell } from "../components/AuthShell";
import { passwordResetFailureMessage } from "../forms/password-reset-messages";
import { passwordResetConfirmSchema } from "../forms/password-reset.schema";
import {
  passwordResetErrorCode,
  useResetPassword,
} from "@olivin/features/auth";

/**
 * Ekran ustawienia nowego hasła: kod z maila + nowe hasło (ADR 0038).
 *
 * Bez deep linku — kod wpisuje użytkownik, a sesję flow resetu niesie
 * `X-Session-Token` zapisany po żądaniu resetu.
 */
export function PasswordResetConfirmScreen() {
  const resetPassword = useResetPassword();
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const failure = resetPassword.isError
    ? passwordResetErrorCode(resetPassword.error)
    : null;

  function handleSubmit() {
    const parsed = passwordResetConfirmSchema.safeParse({ code, password });

    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Sprawdź formularz.");
      return;
    }

    setFormError(null);
    resetPassword.mutate({
      key: parsed.data.code,
      password: parsed.data.password,
    });
  }

  return (
    <AuthShell
      title="Nowe hasło"
      subtitle="Wpisz kod z wiadomości email i ustaw nowe hasło. Po poprawnej zmianie możesz wrócić do logowania."
      footer={
        <Link href="/login">
          <Text className="text-center text-base text-neutral-950 underline">
            Wróć do logowania
          </Text>
        </Link>
      }
    >
      <TextField
        autoCapitalize="characters"
        autoComplete="one-time-code"
        editable={!resetPassword.isPending}
        label="Kod z wiadomości"
        onChangeText={(value) => {
          setCode(value);
          setFormError(null);
        }}
        placeholder="ABCD-EFGH"
        value={code}
      />

      <TextField
        autoComplete="new-password"
        editable={!resetPassword.isPending}
        label="Nowe hasło"
        onChangeText={(value) => {
          setPassword(value);
          setFormError(null);
        }}
        onSubmitEditing={handleSubmit}
        placeholder="Minimum 8 znaków"
        returnKeyType="done"
        secureTextEntry
        value={password}
      />

      {resetPassword.isSuccess ? (
        <Text className="text-sm leading-5 text-emerald-700">
          Hasło zostało zmienione. Możesz się zalogować.
        </Text>
      ) : null}

      <ErrorMessage
        message={
          formError ??
          (failure
            ? passwordResetFailureMessage(
                failure,
                resetPassword.error?.message ?? "Nie udało się ustawić hasła.",
              )
            : null)
        }
      />

      {failure === "codeExpired" ? (
        <Link href="/forgot-password">
          <Text className="text-center text-base text-neutral-950 underline">
            Wyślij nowy kod
          </Text>
        </Link>
      ) : null}

      <Button disabled={resetPassword.isPending} onPress={handleSubmit}>
        {resetPassword.isPending ? "Zapisywanie..." : "Ustaw hasło"}
      </Button>
    </AuthShell>
  );
}
