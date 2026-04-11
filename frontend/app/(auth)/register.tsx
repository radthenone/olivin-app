/**
 * /app/(auth)/register.tsx
 *
 * Ekran rejestracji — 2 kroki:
 * Krok 1: email + hasło (wymagane)
 * Krok 2: profil + adres (opcjonalne — fork-join po signup)
 */
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from "react-native";
import { Link } from "expo-router";
import { useState } from "react";
import { useRegister } from "@features/auth";
import type { RegisterPayload } from "@core/auth";

type Step = 1 | 2;

export default function RegisterScreen() {
  const { register, isLoading, error, clearError } = useRegister();
  const [step, setStep] = useState<Step>(1);

  // Krok 1 — konto
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);

  // Krok 2 — profil (opcjonalne)
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");

  // Krok 2 — adres (opcjonalne)
  const [street, setStreet] = useState("");
  const [city, setCity] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [country, setCountry] = useState("PL");

  // ─── Krok 1: walidacja i przejście do kroku 2 ─────────────────────────────
  const handleNextStep = () => {
    clearError();
    setPasswordError(null);

    if (!email.trim()) return;
    if (password.length < 8) {
      setPasswordError("Hasło musi mieć co najmniej 8 znaków.");
      return;
    }
    if (password !== passwordConfirm) {
      setPasswordError("Hasła nie są identyczne.");
      return;
    }

    setStep(2);
  };

  // ─── Krok 2: wyślij rejestrację ──────────────────────────────────────────
  const handleSubmit = async () => {
    const payload: RegisterPayload = {
      email: email.trim(),
      password,
      // Profil — jeśli cokolwiek wypełnione
      ...(firstName || lastName || phoneNumber
        ? { profile: { firstName, lastName, phoneNumber } }
        : {}),
      // Adres — jeśli cokolwiek wypełnione
      ...(street || city || postalCode
        ? { address: { street, city, postalCode, country, isDefault: true } }
        : {}),
    };

    await register(payload);
  };

  return (
    <KeyboardAvoidingView
      className="flex-1 bg-white"
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView
        contentContainerClassName="flex-1 justify-center px-6 py-12"
        keyboardShouldPersistTaps="handled"
      >
        {/* Header */}
        <View className="mb-8">
          <Text className="text-3xl font-bold text-gray-900 mb-2">
            {step === 1 ? "Utwórz konto" : "Uzupełnij profil"}
          </Text>
          <Text className="text-base text-gray-500">
            {step === 1
              ? "Podaj swój e-mail i hasło"
              : "Opcjonalnie — możesz to zrobić później"}
          </Text>

          {/* Wskaźnik kroków */}
          <View className="flex-row gap-2 mt-4">
            {([1, 2] as Step[]).map((s) => (
              <View
                key={s}
                className={`h-1.5 flex-1 rounded-full ${
                  s <= step ? "bg-blue-600" : "bg-gray-200"
                }`}
              />
            ))}
          </View>
        </View>

        {/* Błąd API */}
        {error && (
          <View className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl">
            <Text className="text-red-700 text-sm">{error}</Text>
          </View>
        )}

        {/* ─── KROK 1: Dane konta ─────────────────────────────────────────── */}
        {step === 1 && (
          <View className="gap-4">
            <FormField
              label="E-mail *"
              value={email}
              onChangeText={(t) => { setEmail(t); clearError(); }}
              placeholder="jan@example.com"
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
            />
            <FormField
              label="Hasło *"
              value={password}
              onChangeText={(t) => { setPassword(t); setPasswordError(null); }}
              placeholder="min. 8 znaków"
              secureTextEntry
              autoComplete="new-password"
              error={passwordError ?? undefined}
            />
            <FormField
              label="Powtórz hasło *"
              value={passwordConfirm}
              onChangeText={(t) => { setPasswordConfirm(t); setPasswordError(null); }}
              placeholder="••••••••"
              secureTextEntry
              autoComplete="new-password"
            />

            <TouchableOpacity
              className="bg-blue-600 rounded-xl py-4 items-center mt-2 active:bg-blue-700"
              onPress={handleNextStep}
            >
              <Text className="text-white font-semibold text-base">Dalej →</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* ─── KROK 2: Profil + Adres (opcjonalne) ───────────────────────── */}
        {step === 2 && (
          <View className="gap-4">
            {/* Profil */}
            <Text className="text-sm font-semibold text-gray-400 uppercase tracking-widest">
              Profil
            </Text>
            <View className="flex-row gap-3">
              <View className="flex-1">
                <FormField
                  label="Imię"
                  value={firstName}
                  onChangeText={setFirstName}
                  placeholder="Jan"
                  autoComplete="given-name"
                />
              </View>
              <View className="flex-1">
                <FormField
                  label="Nazwisko"
                  value={lastName}
                  onChangeText={setLastName}
                  placeholder="Kowalski"
                  autoComplete="family-name"
                />
              </View>
            </View>
            <FormField
              label="Telefon"
              value={phoneNumber}
              onChangeText={setPhoneNumber}
              placeholder="+48 123 456 789"
              keyboardType="phone-pad"
              autoComplete="tel"
            />

            {/* Adres */}
            <Text className="text-sm font-semibold text-gray-400 uppercase tracking-widest mt-2">
              Adres (opcjonalny)
            </Text>
            <FormField
              label="Ulica"
              value={street}
              onChangeText={setStreet}
              placeholder="ul. Przykładowa 1"
              autoComplete="street-address"
            />
            <View className="flex-row gap-3">
              <View className="flex-1">
                <FormField
                  label="Miasto"
                  value={city}
                  onChangeText={setCity}
                  placeholder="Warszawa"
                  autoComplete="address-level2"
                />
              </View>
              <View className="w-28">
                <FormField
                  label="Kod poczt."
                  value={postalCode}
                  onChangeText={setPostalCode}
                  placeholder="00-001"
                  keyboardType="numeric"
                  autoComplete="postal-code"
                />
              </View>
            </View>

            {/* Przyciski */}
            <TouchableOpacity
              className={`rounded-xl py-4 items-center mt-2 ${
                isLoading ? "bg-blue-400" : "bg-blue-600 active:bg-blue-700"
              }`}
              onPress={handleSubmit}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text className="text-white font-semibold text-base">
                  Zarejestruj się
                </Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              onPress={() => setStep(1)}
              className="items-center py-2"
              disabled={isLoading}
            >
              <Text className="text-gray-500 text-sm">← Wróć</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Link do logowania */}
        {step === 1 && (
          <View className="flex-row justify-center mt-8">
            <Text className="text-gray-500 text-sm">Masz już konto? </Text>
            <Link href="/(auth)/login">
              <Text className="text-blue-600 font-medium text-sm">Zaloguj się</Text>
            </Link>
          </View>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// ─── Komponent pomocniczy FormField ───────────────────────────────────────────
interface FormFieldProps {
  label: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  secureTextEntry?: boolean;
  keyboardType?: React.ComponentProps<typeof TextInput>["keyboardType"];
  autoCapitalize?: React.ComponentProps<typeof TextInput>["autoCapitalize"];
  autoComplete?: React.ComponentProps<typeof TextInput>["autoComplete"];
  error?: string;
  returnKeyType?: React.ComponentProps<typeof TextInput>["returnKeyType"];
  onSubmitEditing?: () => void;
  editable?: boolean;
}

function FormField({
  label,
  error,
  editable = true,
  ...inputProps
}: FormFieldProps) {
  return (
    <View>
      <Text className="text-sm font-medium text-gray-700 mb-1.5">{label}</Text>
      <TextInput
        className={`border rounded-xl px-4 py-3 text-base text-gray-900 bg-gray-50 ${
          error ? "border-red-400" : "border-gray-300 focus:border-blue-500"
        }`}
        editable={editable}
        {...inputProps}
      />
      {error && (
        <Text className="text-red-500 text-xs mt-1">{error}</Text>
      )}
    </View>
  );
}
