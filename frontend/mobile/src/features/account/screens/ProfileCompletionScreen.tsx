import { useState } from "react";
import { Text, View } from "react-native";
import { useRouter } from "expo-router";
import { ErrorMessage } from "@ui/feedback/ErrorMessage";
import { Screen } from "@ui/layout/Screen";
import { Button } from "@ui/primitives/Button";
import { TextField } from "@ui/primitives/TextField";
import { profileRequiredSchema } from "../forms/profile-required.schema";
import { useCurrentProfile } from "../hooks/use-current-profile";
import { useSaveRequiredProfile } from "../hooks/use-save-required-profile";

type ProfileCompletionValues = {
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  phoneNumber: string;
};

function ProfileCompletionForm({
  initial,
}: {
  initial: ProfileCompletionValues;
}) {
  const router = useRouter();
  const saveProfile = useSaveRequiredProfile();
  const [firstName, setFirstName] = useState(initial.firstName);
  const [lastName, setLastName] = useState(initial.lastName);
  const [dateOfBirth, setDateOfBirth] = useState(initial.dateOfBirth);
  const [phoneNumber, setPhoneNumber] = useState(initial.phoneNumber);
  const [formError, setFormError] = useState<string | null>(null);

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

/**
 * Ekran uzupełnienia danych profilu wymaganych przez aplikację.
 *
 * Formularz jest montowany od nowa (`key`) po zmianie danych z zapytania,
 * żeby wartości początkowe pochodziły z inicjalizatora `useState`, a nie
 * z efektu kopiującego server state do stanu lokalnego.
 */
export function ProfileCompletionScreen() {
  const profile = useCurrentProfile();
  const initial: ProfileCompletionValues = {
    firstName: profile.data?.firstName ?? "",
    lastName: profile.data?.lastName ?? "",
    dateOfBirth: profile.data?.dateOfBirth ?? "",
    phoneNumber: profile.data?.phoneNumber ?? "",
  };

  return (
    <ProfileCompletionForm key={JSON.stringify(initial)} initial={initial} />
  );
}
