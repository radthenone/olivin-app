import { Text, TextInput, View, type TextInputProps } from "react-native";
import { cn } from "@core/styles/cn";

type TextFieldProps = TextInputProps & {
  label?: string;
  error?: string;
};

/**
 * Bazowe pole tekstowe formularzy.
 *
 * Dlaczego istnieje:
 * formularze auth, profilu i adresów mają wspólny sposób renderowania
 * etykiety, inputa i błędu walidacji.
 */
export function TextField({
  label,
  error,
  className,
  ...props
}: TextFieldProps) {
  return (
    <View className="gap-1">
      {label ? <Text className="text-sm font-medium">{label}</Text> : null}
      <TextInput
        className={cn(
          "h-12 rounded-md border border-neutral-300 bg-white px-3 py-0 text-base text-neutral-950",
          error && "border-red-500",
          className,
        )}
        placeholderTextColor="#737373"
        {...props}
        showSoftInputOnFocus
      />
      {error ? <Text className="text-sm text-red-600">{error}</Text> : null}
    </View>
  );
}
