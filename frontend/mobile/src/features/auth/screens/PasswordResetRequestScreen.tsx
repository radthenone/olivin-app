import { useState } from "react";
import { Text } from "react-native";
import { Link, useRouter } from "expo-router";
import { ErrorMessage } from "@ui/feedback/ErrorMessage";
import { Button } from "@ui/primitives/Button";
import { TextField } from "@ui/primitives/TextField";
import { AuthShell } from "../components/AuthShell";
import { passwordResetRequestSchema } from "../forms/password-reset.schema";
import { useRequestPasswordReset } from "@olivin/features/auth";

/**
 * Ekran rozpoczęcia resetu hasła.
 */
export function PasswordResetRequestScreen() {
  const router = useRouter();
  const requestReset = useRequestPasswordReset();
  const [email, setEmail] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  function handleSubmit() {
    const parsed = passwordResetRequestSchema.safeParse({ email });

    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Sprawdź email.");
      return;
    }

    setFormError(null);
    requestReset.mutate(parsed.data, {
      onSuccess: () => router.push("/reset-password"),
    });
  }

  return (
    <AuthShell
      title="Reset hasła"
      subtitle="Podaj email konta. Jeśli istnieje, wyślemy kod do ustawienia nowego hasła."
      footer={
        <Link href="/login">
          <Text className="text-center text-base text-neutral-950 underline">
            Wróć do logowania
          </Text>
        </Link>
      }
    >
      <TextField
        autoCapitalize="none"
        autoComplete="email"
        editable={!requestReset.isPending}
        keyboardType="email-address"
        label="Email"
        onChangeText={(value) => {
          setEmail(value);
          setFormError(null);
        }}
        onSubmitEditing={handleSubmit}
        placeholder="email@example.com"
        returnKeyType="done"
        value={email}
      />

      <ErrorMessage
        message={
          formError ??
          (requestReset.isError ? "Nie udało się wysłać resetu hasła." : null)
        }
      />

      <Button disabled={requestReset.isPending} onPress={handleSubmit}>
        {requestReset.isPending ? "Wysyłanie..." : "Wyślij kod"}
      </Button>
    </AuthShell>
  );
}
