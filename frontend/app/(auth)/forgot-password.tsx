/**
 * /app/(auth)/forgot-password.tsx
 *
 * Ekran resetu hasła — krok 1: wpisz e-mail.
 * Krok 2 (po kliknięciu linku z maila) to osobna trasa w Expo Router.
 */
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { Link } from "expo-router";
import { useState } from "react";
import { usePasswordReset } from "@features/auth";

export default function ForgotPasswordScreen() {
  const { requestReset, isLoading, isSuccess, error, clearError } =
    usePasswordReset();
  const [email, setEmail] = useState("");

  const handleSubmit = async () => {
    if (!email.trim()) return;
    await requestReset({ email: email.trim() });
  };

  if (isSuccess) {
    return (
      <View className="flex-1 bg-white justify-center px-6">
        <Text className="text-5xl mb-4">📧</Text>
        <Text className="text-3xl font-bold text-gray-900 mb-3">
          Sprawdź skrzynkę
        </Text>
        <Text className="text-base text-gray-500 leading-6 mb-8">
          Jeśli konto o adresie {email} istnieje, wysłaliśmy na nie link do
          zresetowania hasła.
        </Text>
        <Link href="/(auth)/login">
          <Text className="text-blue-600 font-medium text-center">
            Wróć do logowania
          </Text>
        </Link>
      </View>
    );
  }

  return (
    <View className="flex-1 bg-white justify-center px-6">
      <View className="mb-10">
        <Text className="text-3xl font-bold text-gray-900 mb-2">
          Zapomniałeś hasła?
        </Text>
        <Text className="text-base text-gray-500 leading-6">
          Wpisz swój e-mail a wyślemy Ci link do zresetowania hasła.
        </Text>
      </View>

      {error && (
        <View className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl">
          <Text className="text-red-700 text-sm">{error}</Text>
        </View>
      )}

      <View className="mb-6">
        <Text className="text-sm font-medium text-gray-700 mb-1.5">E-mail</Text>
        <TextInput
          className="border border-gray-300 rounded-xl px-4 py-3 text-base text-gray-900 bg-gray-50 focus:border-blue-500"
          placeholder="jan@example.com"
          value={email}
          onChangeText={(t) => { setEmail(t); clearError(); }}
          keyboardType="email-address"
          autoCapitalize="none"
          autoComplete="email"
          returnKeyType="done"
          onSubmitEditing={handleSubmit}
          editable={!isLoading}
        />
      </View>

      <TouchableOpacity
        className={`rounded-xl py-4 items-center mb-4 ${
          isLoading ? "bg-blue-400" : "bg-blue-600 active:bg-blue-700"
        }`}
        onPress={handleSubmit}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text className="text-white font-semibold text-base">
            Wyślij link reset
          </Text>
        )}
      </TouchableOpacity>

      <Link href="/(auth)/login" className="items-center">
        <Text className="text-gray-500 text-sm text-center">
          ← Wróć do logowania
        </Text>
      </Link>
    </View>
  );
}
