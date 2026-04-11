/**
 * /app/(auth)/login.tsx
 *
 * Ekran logowania — działa na Expo Web i Android.
 * Używa useLogin() hook + TextInput z React Native.
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
import { useLogin } from "@features/auth";

export default function LoginScreen() {
  const { login, isLoading, error, clearError } = useLogin();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async () => {
    if (!email.trim() || !password) return;
    await login({ email: email.trim(), password });
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
        {/* Nagłówek */}
        <View className="mb-10">
          <Text className="text-3xl font-bold text-gray-900 mb-2">
            Witaj z powrotem
          </Text>
          <Text className="text-base text-gray-500">
            Zaloguj się do swojego konta
          </Text>
        </View>

        {/* Błąd */}
        {error && (
          <View className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl">
            <Text className="text-red-700 text-sm">{error}</Text>
            <TouchableOpacity onPress={clearError} className="mt-1">
              <Text className="text-red-500 text-xs underline">Zamknij</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Pola formularza */}
        <View className="gap-4 mb-6">
          <View>
            <Text className="text-sm font-medium text-gray-700 mb-1.5">
              E-mail
            </Text>
            <TextInput
              className="border border-gray-300 rounded-xl px-4 py-3 text-base text-gray-900 bg-gray-50 focus:border-blue-500"
              placeholder="jan@example.com"
              value={email}
              onChangeText={(t) => { setEmail(t); clearError(); }}
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
              returnKeyType="next"
              editable={!isLoading}
            />
          </View>

          <View>
            <Text className="text-sm font-medium text-gray-700 mb-1.5">
              Hasło
            </Text>
            <TextInput
              className="border border-gray-300 rounded-xl px-4 py-3 text-base text-gray-900 bg-gray-50 focus:border-blue-500"
              placeholder="••••••••"
              value={password}
              onChangeText={(t) => { setPassword(t); clearError(); }}
              secureTextEntry
              autoComplete="current-password"
              returnKeyType="done"
              onSubmitEditing={handleSubmit}
              editable={!isLoading}
            />
          </View>
        </View>

        {/* Link "Zapomniałem hasła" */}
        <Link href="/(auth)/forgot-password" className="mb-6 self-end">
          <Text className="text-sm text-blue-600">Nie pamiętam hasła</Text>
        </Link>

        {/* Przycisk Zaloguj */}
        <TouchableOpacity
          className={`rounded-xl py-4 items-center ${
            isLoading ? "bg-blue-400" : "bg-blue-600 active:bg-blue-700"
          }`}
          onPress={handleSubmit}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text className="text-white font-semibold text-base">Zaloguj się</Text>
          )}
        </TouchableOpacity>

        {/* Link do rejestracji */}
        <View className="flex-row justify-center mt-8">
          <Text className="text-gray-500 text-sm">Nie masz konta? </Text>
          <Link href="/(auth)/register">
            <Text className="text-blue-600 font-medium text-sm">Zarejestruj się</Text>
          </Link>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
