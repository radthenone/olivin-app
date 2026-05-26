import { Text } from "react-native";

type ErrorMessageProps = {
  message?: string | null;
};

/**
 * Renderuje komunikat błędu dla formularzy i ekranów.
 *
 * Dlaczego istnieje:
 * UI błędów powinien być spójny, a ekrany nie powinny duplikować
 * warunkowego renderowania pustych komunikatów.
 */
export function ErrorMessage({ message }: ErrorMessageProps) {
  if (!message) return null;

  return <Text className="text-sm text-red-600">{message}</Text>;
}
