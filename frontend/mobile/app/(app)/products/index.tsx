import { View } from "react-native";
import { Screen } from "@ui/layout/Screen";
import { ProductListScreen } from "@features/catalog/components/ProductListScreen";

/**
 * Trasa listy produktów w katalogu mobilnym.
 */
export default function ProductsRoute() {
  return (
    <Screen className="px-0 py-0">
      <View className="flex-1">
        <ProductListScreen />
      </View>
    </Screen>
  );
}
