import { Text, View } from "react-native";
import { useTranslations } from "use-intl";
import { CatalogError } from "@olivin/features/catalog";
import { Button } from "@ui/primitives/Button";

export interface ProductErrorViewProps {
  onRetry: () => void;
  error?: unknown;
}

/**
 * Widok błędu katalogu z przyciskiem ponowienia próby.
 *
 * Komunikat pochodzi zawsze z i18n: brak sieci albo błąd ogólny. Surowy
 * `message` błędu (np. status HTTP) nie trafia do interfejsu.
 */
export function ProductErrorView({ onRetry, error }: ProductErrorViewProps) {
  const t = useTranslations("catalog");

  return (
    <View className="flex-1 items-center justify-center gap-4 p-6">
      <Text className="text-center text-lg font-semibold text-neutral-800">
        {error instanceof CatalogError && error.isNetworkError
          ? t("error.network")
          : t("error.general")}
      </Text>
      <Button onPress={onRetry} variant="primary">
        {t("error.retry")}
      </Button>
    </View>
  );
}
