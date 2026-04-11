/**
 * /app/(auth)/verify-email.tsx
 *
 * Ekran weryfikacji e-mail — użytkownik wpisuje kod z wiadomości.
 */
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { useState } from "react";
import { useEmailVerification } from "@features/auth";

export default function VerifyEmailScreen() {
  const { verifyEmail, resend, isVerifying, isResending, error, clearError } =
    useEmailVerification();
  const [code, setCode] = useState("");

  const handleVerify = async () => {
    if (!code.trim()) return;
    await verifyEmail(code.trim());
  };

  return (
    <View className="flex-1 bg-white justify-center px-6">
      {/* Nagłówek */}
      <View className="mb-10">
        <Text className="text-5xl mb-4">📬</Text>
        <Text className="text-3xl font-bold text-gray-900 mb-2">
          Sprawdź e-mail
        </Text>
        <Text className="text-base text-gray-500 leading-6">
          Wysłaliśmy kod weryfikacyjny na Twój adres e-mail. Wpisz go poniżej.
        </Text>
      </View>

      {/* Błąd */}
      {error && (
        <View className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl">
          <Text className="text-red-700 text-sm">{error}</Text>
        </View>
      )}

      {/* Pole kodu */}
      <View className="mb-6">
        <Text className="text-sm font-medium text-gray-700 mb-1.5">
          Kod weryfikacyjny
        </Text>
        <TextInput
          className="border border-gray-300 rounded-xl px-4 py-4 text-2xl text-center tracking-widest text-gray-900 bg-gray-50 focus:border-blue-500"
          placeholder="000000"
          value={code}
          onChangeText={(t) => { setCode(t); clearError(); }}
          keyboardType="number-pad"
          maxLength={8}
          autoComplete="one-time-code"
          returnKeyType="done"
          onSubmitEditing={handleVerify}
          editable={!isVerifying}
        />
      </View>

      {/* Przycisk Weryfikuj */}
      <TouchableOpacity
        className={`rounded-xl py-4 items-center mb-4 ${
          isVerifying ? "bg-blue-400" : "bg-blue-600 active:bg-blue-700"
        }`}
        onPress={handleVerify}
        disabled={isVerifying}
      >
        {isVerifying ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text className="text-white font-semibold text-base">Zweryfikuj</Text>
        )}
      </TouchableOpacity>

      {/* Resend */}
      <TouchableOpacity
        className="items-center py-2"
        onPress={resend}
        disabled={isResending}
      >
        {isResending ? (
          <ActivityIndicator color="#3b82f6" size="small" />
        ) : (
          <Text className="text-blue-600 text-sm">Wyślij ponownie</Text>
        )}
      </TouchableOpacity>
    </View>
  );
}
