import { Text, View } from "react-native";
import { useTranslations } from "use-intl";
import { Button } from "@ui/primitives/Button";

export interface ProductErrorViewProps {
  onRetry: () => void;
  message?: string;
}

/**
 * Widok błędu sieciowego z przyciskiem ponowienia próby.
 */
export function ProductErrorView({ onRetry, message }: ProductErrorViewProps) {
  const t = useTranslations("catalog");

  return (
    <View className="flex-1 items-center justify-center gap-4 p-6">
      <Text className="text-center text-lg font-semibold text-neutral-800">
        {message ?? t("error.network")}
      </Text>
      <Button onPress={onRetry} variant="primary">
        {t("error.retry")}
      </Button>
    </View>
  );
}
