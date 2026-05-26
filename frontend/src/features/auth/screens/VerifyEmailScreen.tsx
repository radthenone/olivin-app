import { useState } from "react";
import { Text } from "react-native";
import { Link, useLocalSearchParams } from "expo-router";
import { ErrorMessage } from "@ui/feedback/ErrorMessage";
import { Button } from "@ui/primitives/Button";
import { TextField } from "@ui/primitives/TextField";
import { AuthShell } from "../components/AuthShell";
import { useVerifyEmail } from "../hooks/use-verify-email";

/**
 * Ekran weryfikacji email.
 *
 * Dlaczego istnieje:
 * backend allauth wymaga potwierdzenia kodu po signup, zanim sesja
 * stanie się w pełni uwierzytelniona.
 */
export function VerifyEmailScreen() {
  const params = useLocalSearchParams<{ key?: string }>();
  const verifyEmail = useVerifyEmail();
  const [key, setKey] = useState(params.key ?? "");

  function handleSubmit() {
    verifyEmail.mutate({ key });
  }

  return (
    <AuthShell
      title="Potwierdź email"
      subtitle="Wpisz kod albo klucz weryfikacyjny z wiadomości email, aby dokończyć aktywację konta."
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
        editable={!verifyEmail.isPending}
        label="Kod weryfikacyjny"
        onChangeText={setKey}
        onSubmitEditing={handleSubmit}
        placeholder="Kod z wiadomości"
        returnKeyType="done"
        value={key}
      />

      <ErrorMessage
        message={
          verifyEmail.isError ? "Nie udało się potwierdzić emaila." : null
        }
      />

      <Button disabled={verifyEmail.isPending || !key} onPress={handleSubmit}>
        {verifyEmail.isPending ? "Potwierdzanie..." : "Potwierdź email"}
      </Button>
    </AuthShell>
  );
}
