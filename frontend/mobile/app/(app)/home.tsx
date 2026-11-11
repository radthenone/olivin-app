import { View } from "react-native";
import { Screen } from "@ui/layout/Screen";
import { ProductListScreen } from "@features/catalog/components/ProductListScreen";

/**
 * Główny ekran aplikacji po zalogowaniu.
 *
 * Prezentuje katalog produktów z nieskończonym przewijaniem i odświeżaniem gestem.
 */
export default function HomeRoute() {
  return (
    <Screen className="px-0 py-0">
      <View className="flex-1">
        <ProductListScreen />
      </View>
    </Screen>
  );
}
