import { useState } from "react";
import { Text } from "react-native";
import { z } from "zod";
import { useAuthContext } from "@core/auth/auth.provider";
import { ErrorMessage } from "@ui/feedback/ErrorMessage";
import { Button } from "@ui/primitives/Button";
import { TextField } from "@ui/primitives/TextField";
import { AuthShell } from "../components/AuthShell";
import { ConsentSwitches } from "../components/ConsentSwitches";
import {
  NO_CONSENTS,
  signupConsentsSchema,
  toSignupConsentsBody,
} from "../forms/register.schema";
import { useProviderSignup } from "../hooks/use-provider-signup";

const providerSignupSchema = signupConsentsSchema.extend({
  email: z.email("Podaj poprawny adres email."),
});

/**
 * Dokończenie rejestracji po Google/Facebook.
 *
 * Dlaczego istnieje:
 * konto z logowania zewnętrznego nie powstaje samo — klient musi
 * zaakceptować regulamin i politykę prywatności (#207).
 */
export function ProviderSignupScreen() {
  const auth = useAuthContext();
  const signup = useProviderSignup();
  const [email, setEmail] = useState("");
  const [consents, setConsents] = useState(NO_CONSENTS);
  const [formError, setFormError] = useState<string | null>(null);

  function handleSubmit() {
    const parsed = providerSignupSchema.safeParse({ email, ...consents });

    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Sprawdź dane.");
      return;
    }

    setFormError(null);
    signup.mutate({
      email: parsed.data.email,
      ...toSignupConsentsBody(parsed.data),
    });
  }

  return (
    <AuthShell
      title="Dokończ rejestrację"
      subtitle="Zakładasz konto przez zewnętrznego dostawcę. Potwierdź adres email i zaakceptuj wymagane zgody."
      footer={
        <Text
          className="text-center text-base text-neutral-950 underline"
          onPress={() => auth.logout.mutate()}
        >
          Anuluj
        </Text>
      }
    >
      <TextField
        autoCapitalize="none"
        autoComplete="email"
        editable={!signup.isPending}
        keyboardType="email-address"
        label="Email"
        onChangeText={(value) => {
          setEmail(value);
          setFormError(null);
        }}
        placeholder="jan@example.com"
        returnKeyType="done"
        value={email}
      />
      <ConsentSwitches
        disabled={signup.isPending}
        onChange={(next) => {
          setConsents(next);
          setFormError(null);
        }}
        value={consents}
      />

      <ErrorMessage
        message={formError ?? (signup.isError ? signup.error.message : null)}
      />

      <Button disabled={signup.isPending} onPress={handleSubmit}>
        {signup.isPending ? "Tworzenie konta..." : "Załóż konto"}
      </Button>
    </AuthShell>
  );
}
