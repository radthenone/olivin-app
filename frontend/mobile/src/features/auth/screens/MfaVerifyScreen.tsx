import { useState } from "react";
import { Text } from "react-native";
import { Link } from "expo-router";
import { ErrorMessage } from "@ui/feedback/ErrorMessage";
import { Button } from "@ui/primitives/Button";
import { TextField } from "@ui/primitives/TextField";
import { AuthShell } from "../components/AuthShell";
import { mfaSchema } from "../forms/mfa.schema";
import { useMfaAuthenticate } from "../hooks/use-mfa-authenticate";

/**
 * Ekran potwierdzenia MFA po logowaniu.
 */
export function MfaVerifyScreen() {
  const mfa = useMfaAuthenticate();
  const [code, setCode] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  function handleSubmit() {
    const parsed = mfaSchema.safeParse({ code });

    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Sprawdź kod.");
      return;
    }

    setFormError(null);
    mfa.mutate(parsed.data);
  }

  return (
    <AuthShell
      title="Weryfikacja MFA"
      subtitle="Podaj kod z aplikacji uwierzytelniającej albo kod odzyskiwania, aby dokończyć logowanie."
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
        editable={!mfa.isPending}
        keyboardType="number-pad"
        label="Kod MFA"
        onChangeText={(value) => {
          setCode(value);
          setFormError(null);
        }}
        onSubmitEditing={handleSubmit}
        placeholder="123456"
        returnKeyType="done"
        value={code}
      />

      <ErrorMessage
        message={
          formError ?? (mfa.isError ? "Nie udało się potwierdzić MFA." : null)
        }
      />

      <Button disabled={mfa.isPending} onPress={handleSubmit}>
        {mfa.isPending ? "Sprawdzanie..." : "Potwierdź"}
      </Button>
    </AuthShell>
  );
}
