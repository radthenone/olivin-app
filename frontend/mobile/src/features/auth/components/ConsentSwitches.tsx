import { Switch, Text, View } from "react-native";
import type { SignupConsentsValues } from "../forms/register.schema";

const CONSENTS: [keyof SignupConsentsValues, string][] = [
  ["consentTerms", "Akceptuję regulamin (wymagane)"],
  ["consentPrivacy", "Akceptuję politykę prywatności (wymagane)"],
  ["consentMarketing", "Chcę otrzymywać informacje marketingowe e-mailem"],
];

type ConsentSwitchesProps = {
  value: SignupConsentsValues;
  onChange: (value: SignupConsentsValues) => void;
  disabled?: boolean;
};

/**
 * Przełączniki zgód przy zakładaniu konta.
 *
 * Dlaczego istnieje:
 * rejestracja e-mailem i dokończenie rejestracji po Google/Facebook
 * wymagają tych samych zgód (#207).
 */
export function ConsentSwitches({
  value,
  onChange,
  disabled,
}: ConsentSwitchesProps) {
  return (
    <>
      {CONSENTS.map(([key, label]) => (
        <View className="flex-row items-center gap-3" key={key}>
          <Switch
            accessibilityLabel={label}
            disabled={disabled}
            onValueChange={(next) => onChange({ ...value, [key]: next })}
            value={value[key]}
          />
          <Text className="flex-1 text-base text-neutral-950">{label}</Text>
        </View>
      ))}
    </>
  );
}
