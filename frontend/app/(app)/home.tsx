import { Text, View } from "react-native";
import { useAuthContext } from "@core/auth/auth.provider";
import { Button } from "@ui/primitives/Button";
import { Screen } from "@ui/layout/Screen";
import { useRouter } from "expo-router";

/**
 * Pierwszy ekran po zalogowaniu.
 *
 * Dlaczego istnieje:
 * służy jako minimalny test pełnego przepływu session -> protected route.
 */
export default function HomeRoute() {
  const auth = useAuthContext();
  const router = useRouter();

  return (
    <Screen>
      <View className="gap-4">
        <Text className="text-2xl font-semibold">Olivin</Text>
        <Text className="text-base text-neutral-700">
          {auth.user?.email ?? "Zalogowany użytkownik"}
        </Text>
        <Button
          onPress={() => router.push("/account-settings")}
          variant="outline"
        >
          Ustawienia konta
        </Button>
        <Button
          disabled={auth.logout.isPending}
          onPress={() => auth.logout.mutate()}
        >
          {auth.logout.isPending ? "Wylogowywanie..." : "Wyloguj"}
        </Button>
      </View>
    </Screen>
  );
}
