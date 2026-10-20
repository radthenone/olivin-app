import { useState } from "react";
import { Text, View } from "react-native";
import { useRouter } from "expo-router";
import { ErrorMessage } from "@ui/feedback/ErrorMessage";
import { Screen } from "@ui/layout/Screen";
import { Button } from "@ui/primitives/Button";
import { TextField } from "@ui/primitives/TextField";
import {
  profileRequiredSchema,
  type ProfileRequiredFormValues,
} from "../forms/profile-required.schema";
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
  isSaving,
  isSaveError,
  onSubmit,
}: {
  initial: ProfileCompletionValues;
  isSaving: boolean;
  isSaveError: boolean;
  onSubmit: (values: ProfileRequiredFormValues) => void;
}) {
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
    onSubmit(parsed.data);
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
            editable={!isSaving}
            label="Imię"
            onChangeText={(value) => {
              setFirstName(value);
              setFormError(null);
            }}
            placeholder="Jan"
            value={firstName}
          />
          <TextField
            editable={!isSaving}
            label="Nazwisko"
            onChangeText={(value) => {
              setLastName(value);
              setFormError(null);
            }}
            placeholder="Kowalski"
            value={lastName}
          />
          <TextField
            editable={!isSaving}
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
            editable={!isSaving}
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
              (isSaveError ? "Nie udało się zapisać danych profilu." : null)
            }
          />

          <Button disabled={isSaving} onPress={handleSubmit}>
            {isSaving ? "Zapisywanie..." : "Zapisz i przejdź dalej"}
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
  const router = useRouter();
  const profile = useCurrentProfile();
  const saveProfile = useSaveRequiredProfile();
  const initial: ProfileCompletionValues = {
    firstName: profile.data?.firstName ?? "",
    lastName: profile.data?.lastName ?? "",
    dateOfBirth: profile.data?.dateOfBirth ?? "",
    phoneNumber: profile.data?.phoneNumber ?? "",
  };

  return (
    <ProfileCompletionForm
      initial={initial}
      isSaveError={saveProfile.isError}
      isSaving={saveProfile.isPending}
      key={JSON.stringify(initial)}
      onSubmit={(values) =>
        // Mutacja i przekierowanie w rodzicu: formularz remountuje się po
        // invalidateQueries, a callback `onSuccess` z `mutate` przepadłby.
        saveProfile.mutate(values, {
          onSuccess: () => router.replace("/home"),
        })
      }
    />
  );
}
