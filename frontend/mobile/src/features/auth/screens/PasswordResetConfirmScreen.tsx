import { useState } from "react";
import { Text } from "react-native";
import { Link, useLocalSearchParams } from "expo-router";
import { ErrorMessage } from "@ui/feedback/ErrorMessage";
import { Button } from "@ui/primitives/Button";
import { TextField } from "@ui/primitives/TextField";
import { AuthShell } from "../components/AuthShell";
import { passwordResetConfirmSchema } from "../forms/password-reset.schema";
import { useResetPassword } from "../hooks/use-reset-password";

/**
 * Ekran ustawienia nowego hasła po resecie.
 */
export function PasswordResetConfirmScreen() {
  const params = useLocalSearchParams<{ key?: string }>();
  const resetPassword = useResetPassword();
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  function handleSubmit() {
    const parsed = passwordResetConfirmSchema.safeParse({ password });

    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Sprawdź hasło.");
      return;
    }

    if (!params.key) {
      setFormError("Brakuje klucza resetu hasła.");
      return;
    }

    setFormError(null);
    resetPassword.mutate({ key: params.key, password: parsed.data.password });
  }

  return (
    <AuthShell
      title="Nowe hasło"
      subtitle="Ustaw nowe hasło do konta. Po poprawnej zmianie możesz wrócić do logowania."
      footer={
        <Link href="/login">
          <Text className="text-center text-base text-neutral-950 underline">
            Wróć do logowania
          </Text>
        </Link>
      }
    >
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

      <ErrorMessage
        message={
          formError ??
          (resetPassword.isError ? "Nie udało się ustawić nowego hasła." : null)
        }
      />

      <Button disabled={resetPassword.isPending} onPress={handleSubmit}>
        {resetPassword.isPending ? "Zapisywanie..." : "Ustaw hasło"}
      </Button>
    </AuthShell>
  );
}
