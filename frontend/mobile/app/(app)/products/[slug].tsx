import { View } from "react-native";
import { Screen } from "@ui/layout/Screen";
import { ProductDetailScreen } from "@features/catalog/components/ProductDetailScreen";

/**
 * Trasa karty produktu w katalogu mobilnym.
 */
export default function ProductDetailRoute() {
  return (
    <Screen className="px-0 py-0">
      <View className="flex-1">
        <ProductDetailScreen />
      </View>
    </Screen>
  );
}
