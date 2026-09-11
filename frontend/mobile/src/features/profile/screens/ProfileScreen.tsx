import { Text, View } from "react-native";
import { Screen } from "@ui/layout/Screen";
import { useProfile } from "../hooks/use-profile";

/**
 * Ekran profilu użytkownika.
 *
 * Dlaczego istnieje:
 * pokazuje wzorzec dla danych aplikacyjnych: screen -> hook -> service
 * -> Orval -> backend.
 */
export function ProfileScreen() {
  const profile = useProfile();

  return (
    <Screen>
      <View className="gap-3">
        <Text className="text-xl font-semibold">Profil</Text>
        {profile.isLoading ? <Text>Ładowanie...</Text> : null}
        {profile.data ? (
          <Text>
            {profile.data.firstName} {profile.data.lastName}
          </Text>
        ) : null}
        {profile.isError ? (
          <Text className="text-red-600">Nie udało się pobrać profilu.</Text>
        ) : null}
      </View>
    </Screen>
  );
}
