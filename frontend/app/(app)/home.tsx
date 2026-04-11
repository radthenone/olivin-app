/**
 * /app/(app)/home.tsx
 * Przykładowy ekran dla zalogowanego użytkownika z przyciskiem wylogowania.
 */
import { View, Text, TouchableOpacity, ActivityIndicator } from "react-native";
import { useLogout, useAuth } from "@features/auth";

export default function HomeScreen() {
  const { logout, isLoading } = useLogout();
  const { isAuthenticated } = useAuth();

  return (
    <View className="flex-1 bg-white justify-center px-6">
      <Text className="text-3xl font-bold text-gray-900 mb-2">Witaj! 👋</Text>
      <Text className="text-base text-gray-500 mb-10">
        Jesteś zalogowany: {isAuthenticated ? "tak" : "nie"}
      </Text>

      <TouchableOpacity
        className={`rounded-xl py-4 items-center ${
          isLoading ? "bg-red-300" : "bg-red-500 active:bg-red-600"
        }`}
        onPress={logout}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text className="text-white font-semibold text-base">
            Wyloguj się
          </Text>
        )}
      </TouchableOpacity>
    </View>
  );
}
