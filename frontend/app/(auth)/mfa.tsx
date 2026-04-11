/**
 * /app/(auth)/mfa.tsx
 *
 * Ekran weryfikacji MFA (TOTP lub kody recovery).
 */
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { useState } from "react";
import { useMfa } from "@features/auth";

export default function MfaScreen() {
  const { verifyMfa, isLoading, error, clearError } = useMfa();
  const [code, setCode] = useState("");

  const handleVerify = async () => {
    if (!code.trim()) return;
    await verifyMfa(code.trim());
  };

  return (
    <View className="flex-1 bg-white justify-center px-6">
      <View className="mb-10">
        <Text className="text-5xl mb-4">🔐</Text>
        <Text className="text-3xl font-bold text-gray-900 mb-2">
          Weryfikacja dwuetapowa
        </Text>
        <Text className="text-base text-gray-500 leading-6">
          Wpisz 6-cyfrowy kod z aplikacji uwierzytelniającej lub jeden z kodów odzyskiwania.
        </Text>
      </View>

      {error && (
        <View className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl">
          <Text className="text-red-700 text-sm">{error}</Text>
        </View>
      )}

      <View className="mb-6">
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
          editable={!isLoading}
        />
      </View>

      <TouchableOpacity
        className={`rounded-xl py-4 items-center ${
          isLoading ? "bg-blue-400" : "bg-blue-600 active:bg-blue-700"
        }`}
        onPress={handleVerify}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text className="text-white font-semibold text-base">
            Potwierdź kod
          </Text>
        )}
      </TouchableOpacity>
    </View>
  );
}
