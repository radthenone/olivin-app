import { useEffect, useState } from "react";
import { Text, View } from "react-native";
import { useRouter } from "expo-router";
import { ErrorMessage } from "@ui/feedback/ErrorMessage";
import { Screen } from "@ui/layout/Screen";
import { Button } from "@ui/primitives/Button";
import { TextField } from "@ui/primitives/TextField";
import { profileRequiredSchema } from "../forms/profile-required.schema";
import { useCurrentProfile } from "../hooks/use-current-profile";
import { useSaveRequiredProfile } from "../hooks/use-save-required-profile";

/**
 * Ekran uzupełnienia danych profilu wymaganych przez aplikację.
 */
export function ProfileCompletionScreen() {
  const router = useRouter();
  const profile = useCurrentProfile();
  const saveProfile = useSaveRequiredProfile();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (!profile.data) return;

    setFirstName(profile.data.firstName ?? "");
    setLastName(profile.data.lastName ?? "");
    setDateOfBirth(profile.data.dateOfBirth ?? "");
    setPhoneNumber(profile.data.phoneNumber ?? "");
  }, [profile.data]);

  function handleSubmit() {
    const parsed = profileRequiredSchema.safeParse({
      firstName,
      lastName,
      dateOfBirth,
      phoneNumber,
    });

    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Sprawdź dane profilu.");
      return;
    }

    setFormError(null);
    saveProfile.mutate(parsed.data, {
      onSuccess: () => router.replace("/home"),
    });
  }

  return (
    <Screen>
      <View className="flex-1 justify-center gap-6 web:mx-auto web:w-full web:max-w-md">
        <View className="gap-2">
          <Text className="text-3xl font-semibold text-neutral-950">
            Uzupełnij profil
          </Text>
          <Text className="text-base leading-6 text-neutral-600">
            Te dane będą używane przy zamówieniach i obsłudze konta klienta.
          </Text>
        </View>

        <View className="gap-4">
          <TextField
            editable={!saveProfile.isPending}
            label="Imię"
            onChangeText={(value) => {
              setFirstName(value);
              setFormError(null);
            }}
            placeholder="Jan"
            value={firstName}
          />
          <TextField
            editable={!saveProfile.isPending}
            label="Nazwisko"
            onChangeText={(value) => {
              setLastName(value);
              setFormError(null);
            }}
            placeholder="Kowalski"
            value={lastName}
          />
          <TextField
            editable={!saveProfile.isPending}
            label="Data urodzenia"
            onChangeText={(value) => {
              setDateOfBirth(value);
              setFormError(null);
            }}
            placeholder="1990-01-15"
            returnKeyType="next"
            value={dateOfBirth}
          />
          <TextField
            editable={!saveProfile.isPending}
            keyboardType="phone-pad"
            label="Telefon"
            onChangeText={(value) => {
              setPhoneNumber(value);
              setFormError(null);
            }}
            onSubmitEditing={handleSubmit}
            placeholder="+48 123 456 789"
            returnKeyType="done"
            value={phoneNumber}
          />

          <ErrorMessage
            message={
              formError ??
              (saveProfile.isError
                ? "Nie udało się zapisać danych profilu."
                : null)
            }
          />

          <Button disabled={saveProfile.isPending} onPress={handleSubmit}>
            {saveProfile.isPending
              ? "Zapisywanie..."
              : "Zapisz i przejdź dalej"}
          </Button>
        </View>
      </View>
    </Screen>
  );
}
