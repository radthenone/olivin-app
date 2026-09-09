import { useState } from "react";
import { Text } from "react-native";
import { Link } from "expo-router";
import { ErrorMessage } from "@ui/feedback/ErrorMessage";
import { Button } from "@ui/primitives/Button";
import { TextField } from "@ui/primitives/TextField";
import { AuthShell } from "../components/AuthShell";
import { registerSchema } from "../forms/register.schema";
import { useRegister } from "../hooks/use-register";

/**
 * Ekran rejestracji.
 *
 * Dlaczego istnieje:
 * będzie rozwijany po ustabilizowaniu login/session; signup w allauth
 * prowadzi dalej do weryfikacji email.
 */
export function RegisterScreen() {
  const register = useRegister();
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  function handleSubmit() {
    const parsed = registerSchema.safeParse({
      email,
      firstName,
      lastName,
      dateOfBirth,
      phoneNumber,
      password,
      passwordConfirm,
    });

    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Sprawdź dane.");
      return;
    }

    setFormError(null);
    register.mutate({
      email: parsed.data.email,
      firstName: parsed.data.firstName,
      lastName: parsed.data.lastName,
      dateOfBirth: parsed.data.dateOfBirth,
      phoneNumber: parsed.data.phoneNumber,
      password: parsed.data.password,
    });
  }

  return (
    <AuthShell
      title="Utwórz konto"
      subtitle="Załóż konto klienta Olivin. Po rejestracji możesz zostać poproszony o potwierdzenie adresu email."
      footer={
        <Link href="/login">
          <Text className="text-center text-base text-neutral-950 underline">
            Masz już konto? Zaloguj się
          </Text>
        </Link>
      }
    >
      <TextField
        autoCapitalize="none"
        autoComplete="email"
        editable={!register.isPending}
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
        autoComplete="given-name"
        editable={!register.isPending}
        label="Imię"
        onChangeText={(value) => {
          setFirstName(value);
          setFormError(null);
        }}
        placeholder="Jan"
        returnKeyType="next"
        value={firstName}
      />
      <TextField
        autoComplete="family-name"
        editable={!register.isPending}
        label="Nazwisko"
        onChangeText={(value) => {
          setLastName(value);
          setFormError(null);
        }}
        placeholder="Kowalski"
        returnKeyType="next"
        value={lastName}
      />
      <TextField
        editable={!register.isPending}
        label="Data urodzenia"
        onChangeText={(value) => {
          setDateOfBirth(value);
          setFormError(null);
        }}
        placeholder="1990-01-15"
        returnKeyType="next"
        value={dateOfBirth}
      />
      <TextField
        autoComplete="tel"
        editable={!register.isPending}
        keyboardType="phone-pad"
        label="Telefon"
        onChangeText={(value) => {
          setPhoneNumber(value);
          setFormError(null);
        }}
        placeholder="+48 123 456 789"
        returnKeyType="next"
        value={phoneNumber}
      />
      <TextField
        autoComplete="new-password"
        editable={!register.isPending}
        label="Hasło"
        onChangeText={(value) => {
          setPassword(value);
          setFormError(null);
        }}
        placeholder="Minimum 8 znaków"
        returnKeyType="next"
        secureTextEntry
        value={password}
      />
      <TextField
        autoComplete="new-password"
        editable={!register.isPending}
        label="Powtórz hasło"
        onChangeText={(value) => {
          setPasswordConfirm(value);
          setFormError(null);
        }}
        onSubmitEditing={handleSubmit}
        placeholder="Powtórz hasło"
        returnKeyType="done"
        secureTextEntry
        value={passwordConfirm}
      />

      <ErrorMessage
        message={
          formError ??
          (register.isError ? "Nie udało się utworzyć konta." : null)
        }
      />

      <Button disabled={register.isPending} onPress={handleSubmit}>
        {register.isPending ? "Tworzenie konta..." : "Zarejestruj"}
      </Button>
    </AuthShell>
  );
}
