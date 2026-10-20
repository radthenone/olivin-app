import { useState } from "react";
import { ScrollView, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { z } from "zod";
import { useAuthContext } from "@core/auth/auth.provider";
import { ApiError } from "@olivin/api";
import { ErrorMessage } from "@ui/feedback/ErrorMessage";
import { Screen } from "@ui/layout/Screen";
import { Button } from "@ui/primitives/Button";
import { TextField } from "@ui/primitives/TextField";
import { TotpQrCode } from "../components/TotpQrCode";
import { changePasswordSchema } from "../forms/change-password.schema";
import { profileEditSchema } from "../forms/profile-edit.schema";
import { setupMfaSchema } from "../forms/setup-mfa.schema";
import { useActivateTotp } from "../hooks/use-activate-totp";
import { useChangePassword } from "../hooks/use-change-password";
import { useCurrentProfile } from "../hooks/use-current-profile";
import { useDeactivateTotp } from "../hooks/use-deactivate-totp";
import { useRequestEmailChange } from "../hooks/use-request-email-change";
import { useSaveProfile } from "../hooks/use-save-profile";
import { useTotpAuthenticator } from "../hooks/use-totp-authenticator";

const emailChangeSchema = z.object({
  email: z.email("Podaj poprawny adres email."),
});

type ProfileEditValues = z.infer<typeof profileEditSchema>;
type EmailChangeValues = z.infer<typeof emailChangeSchema>;

function getApiErrorMessage(error: unknown): string | null {
  if (!(error instanceof ApiError)) {
    return null;
  }

  const responseData = error.response.data as
    | {
        errors?: {
          message?: string;
        }[];
      }
    | undefined;

  return responseData?.errors?.[0]?.message ?? null;
}

function FieldRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <View className="gap-1 border-b border-neutral-200 py-3">
      <Text className="text-xs font-medium uppercase text-neutral-500">
        {label}
      </Text>
      <Text className="text-base text-neutral-950">
        {value || "Brak danych"}
      </Text>
    </View>
  );
}

function ProfileEditForm({
  initial,
  isSaving,
  isSaveError,
  success,
  onSubmit,
}: {
  initial: ProfileEditValues;
  isSaving: boolean;
  isSaveError: boolean;
  success: boolean;
  onSubmit: (values: ProfileEditValues) => void;
}) {
  const [firstName, setFirstName] = useState(initial.firstName);
  const [lastName, setLastName] = useState(initial.lastName);
  const [phoneNumber, setPhoneNumber] = useState(initial.phoneNumber);
  const [formError, setFormError] = useState<string | null>(null);

  function handleSubmit() {
    const parsed = profileEditSchema.safeParse({
      firstName,
      lastName,
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
    <View className="gap-3">
      <Text className="text-lg font-semibold text-neutral-950">
        Edycja profilu
      </Text>
      <TextField
        editable={!isSaving}
        label="Imię"
        onChangeText={(value) => {
          setFirstName(value);
          setFormError(null);
        }}
        value={firstName}
      />
      <TextField
        editable={!isSaving}
        label="Nazwisko"
        onChangeText={(value) => {
          setLastName(value);
          setFormError(null);
        }}
        value={lastName}
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
          formError ?? (isSaveError ? "Nie udało się zapisać profilu." : null)
        }
      />
      {success ? (
        <Text className="text-sm text-green-700">Profil został zapisany.</Text>
      ) : null}
      <Button disabled={isSaving} onPress={handleSubmit}>
        {isSaving ? "Zapisywanie..." : "Zapisz profil"}
      </Button>
    </View>
  );
}

function EmailChangeForm({
  initialEmail,
  isSaving,
  isSaveError,
  success,
  onSubmit,
}: {
  initialEmail: string;
  isSaving: boolean;
  isSaveError: boolean;
  success: boolean;
  onSubmit: (values: EmailChangeValues) => void;
}) {
  const [email, setEmail] = useState(initialEmail);
  const [formError, setFormError] = useState<string | null>(null);

  function handleSubmit() {
    const parsed = emailChangeSchema.safeParse({ email });

    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Sprawdź email.");
      return;
    }

    setFormError(null);
    onSubmit(parsed.data);
  }

  return (
    <View className="gap-3">
      <Text className="text-lg font-semibold text-neutral-950">
        Zmiana emaila
      </Text>
      <TextField
        autoCapitalize="none"
        autoComplete="email"
        editable={!isSaving}
        keyboardType="email-address"
        label="Nowy email"
        onChangeText={(value) => {
          setEmail(value);
          setFormError(null);
        }}
        onSubmitEditing={handleSubmit}
        placeholder="email@example.com"
        returnKeyType="done"
        value={email}
      />
      <ErrorMessage
        message={
          formError ??
          (isSaveError ? "Nie udało się rozpocząć zmiany emaila." : null)
        }
      />
      {success ? (
        <Text className="text-sm text-green-700">
          Wysłano wiadomość potwierdzającą zmianę emaila.
        </Text>
      ) : null}
      <Button disabled={isSaving} onPress={handleSubmit}>
        {isSaving ? "Wysyłanie..." : "Zmień email"}
      </Button>
    </View>
  );
}

/**
 * Ekran ustawień konta użytkownika.
 *
 * Dlaczego istnieje:
 * zbiera dane sesji, profil oraz ustawienia bezpieczeństwa w jednym miejscu,
 * bez przenoszenia server state do lokalnego store.
 *
 * Formularze profilu i emaila są montowane od nowa (`key`) po zmianie danych
 * z zapytania, więc wartości początkowe pochodzą z inicjalizatorów `useState`,
 * a nie z efektów kopiujących server state do stanu lokalnego.
 */
export function AccountSettingsScreen() {
  const router = useRouter();
  const auth = useAuthContext();
  const profile = useCurrentProfile();
  const totp = useTotpAuthenticator();
  const activateTotp = useActivateTotp();
  const deactivateTotp = useDeactivateTotp();
  const changePassword = useChangePassword();
  const saveProfile = useSaveProfile();
  const requestEmailChange = useRequestEmailChange();

  const [profileSuccess, setProfileSuccess] = useState(false);
  const [emailSuccess, setEmailSuccess] = useState(false);
  const [mfaCode, setMfaCode] = useState("");
  const [mfaFormError, setMfaFormError] = useState<string | null>(null);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordFormError, setPasswordFormError] = useState<string | null>(
    null,
  );
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  const displayName =
    profile.data?.fullName || auth.user?.display || auth.user?.email;

  const profileInitial: ProfileEditValues = {
    firstName: profile.data?.firstName ?? "",
    lastName: profile.data?.lastName ?? "",
    phoneNumber: profile.data?.phoneNumber ?? "",
  };

  function handleSaveProfile(values: ProfileEditValues) {
    setProfileSuccess(false);
    saveProfile.mutate(values, {
      onSuccess: () => setProfileSuccess(true),
    });
  }

  function handleRequestEmailChange(values: EmailChangeValues) {
    setEmailSuccess(false);
    requestEmailChange.mutate(values, {
      onSuccess: () => setEmailSuccess(true),
    });
  }

  function handleActivateTotp() {
    const parsed = setupMfaSchema.safeParse({ code: mfaCode });

    if (!parsed.success) {
      setMfaFormError(parsed.error.issues[0]?.message ?? "Sprawdź kod MFA.");
      return;
    }

    setMfaFormError(null);
    activateTotp.mutate(parsed.data, {
      onSuccess: () => {
        setMfaCode("");
      },
    });
  }

  function handleChangePassword() {
    const parsed = changePasswordSchema.safeParse({
      currentPassword,
      newPassword,
    });

    if (!parsed.success) {
      setPasswordFormError(
        parsed.error.issues[0]?.message ?? "Sprawdź dane formularza.",
      );
      return;
    }

    setPasswordFormError(null);
    setPasswordSuccess(false);
    changePassword.mutate(parsed.data, {
      onSuccess: () => {
        setCurrentPassword("");
        setNewPassword("");
        setPasswordSuccess(true);
      },
    });
  }

  const inactiveTotpSetup =
    totp.data?.status === "inactive" ? totp.data.setup : null;

  return (
    <Screen>
      <ScrollView
        className="flex-1"
        contentContainerClassName="gap-6 pb-8"
        keyboardShouldPersistTaps="handled"
      >
        <View className="gap-2">
          <Text className="text-2xl font-semibold text-neutral-950">
            Ustawienia konta
          </Text>
          <Text className="text-base text-neutral-700">
            {displayName ?? "Zalogowany użytkownik"}
          </Text>
          <Button
            onPress={() => router.push("/home")}
            size="sm"
            variant="outline"
          >
            Wróć na główną
          </Button>
        </View>

        <View className="gap-1">
          <Text className="text-lg font-semibold text-neutral-950">
            Dane użytkownika
          </Text>
          {profile.isLoading ? <Text>Ładowanie profilu...</Text> : null}
          <FieldRow label="Email sesji" value={auth.user?.email} />
          <FieldRow label="Nazwa" value={profile.data?.fullName} />
          <FieldRow label="Data urodzenia" value={profile.data?.dateOfBirth} />
          <FieldRow
            label="Wiek"
            value={
              profile.data?.age === null || profile.data?.age === undefined
                ? null
                : String(profile.data.age)
            }
          />
          <FieldRow label="Telefon" value={profile.data?.phoneNumber} />
          <FieldRow label="Rola" value={profile.data?.role} />
          {profile.isError ? (
            <Text className="text-sm text-red-600">
              Nie udało się pobrać profilu użytkownika.
            </Text>
          ) : null}
        </View>

        <ProfileEditForm
          initial={profileInitial}
          isSaveError={saveProfile.isError}
          isSaving={saveProfile.isPending}
          key={JSON.stringify(profileInitial)}
          onSubmit={handleSaveProfile}
          success={profileSuccess}
        />

        <EmailChangeForm
          initialEmail={auth.user?.email ?? ""}
          isSaveError={requestEmailChange.isError}
          isSaving={requestEmailChange.isPending}
          key={auth.user?.email ?? ""}
          onSubmit={handleRequestEmailChange}
          success={emailSuccess}
        />

        <View className="gap-3">
          <Text className="text-lg font-semibold text-neutral-950">
            MFA / TOTP
          </Text>
          {totp.isLoading ? <Text>Sprawdzanie statusu MFA...</Text> : null}
          {totp.data?.status === "active" ? (
            <>
              <Text className="text-base text-neutral-700">
                MFA jest włączone dla tego konta.
              </Text>
              <Button
                disabled={deactivateTotp.isPending}
                onPress={() => deactivateTotp.mutate()}
                variant="outline"
              >
                {deactivateTotp.isPending ? "Wyłączanie..." : "Wyłącz MFA"}
              </Button>
            </>
          ) : null}
          {totp.data?.status === "inactive" ? (
            <>
              <Text className="text-base text-neutral-700">
                Dodaj ten sekret w aplikacji uwierzytelniającej, a potem wpisz
                wygenerowany kod.
              </Text>
              <TotpQrCode uri={inactiveTotpSetup?.totp_url} />
              <FieldRow label="Sekret TOTP" value={inactiveTotpSetup?.secret} />
              <FieldRow label="URI TOTP" value={inactiveTotpSetup?.totp_url} />
              <TextField
                autoCapitalize="none"
                editable={!activateTotp.isPending}
                keyboardType="number-pad"
                label="Kod z aplikacji"
                onChangeText={(value) => {
                  setMfaCode(value);
                  setMfaFormError(null);
                }}
                onSubmitEditing={handleActivateTotp}
                placeholder="123456"
                returnKeyType="done"
                value={mfaCode}
              />
              <ErrorMessage
                message={
                  mfaFormError ??
                  (activateTotp.isError
                    ? (getApiErrorMessage(activateTotp.error) ??
                      "Nie udało się włączyć MFA.")
                    : null)
                }
              />
              <Button
                disabled={activateTotp.isPending}
                onPress={handleActivateTotp}
              >
                {activateTotp.isPending ? "Włączanie..." : "Włącz MFA"}
              </Button>
            </>
          ) : null}
          {totp.data?.status === "unavailable" || totp.isError ? (
            <Text className="text-sm text-red-600">
              Ustawienia MFA są chwilowo niedostępne.
            </Text>
          ) : null}
        </View>

        <View className="gap-3">
          <Text className="text-lg font-semibold text-neutral-950">
            Zmiana hasła
          </Text>
          <TextField
            autoComplete="current-password"
            editable={!changePassword.isPending}
            label="Aktualne hasło"
            onChangeText={(value) => {
              setCurrentPassword(value);
              setPasswordFormError(null);
              setPasswordSuccess(false);
            }}
            placeholder="Aktualne hasło"
            secureTextEntry
            value={currentPassword}
          />
          <TextField
            autoComplete="new-password"
            editable={!changePassword.isPending}
            label="Nowe hasło"
            onChangeText={(value) => {
              setNewPassword(value);
              setPasswordFormError(null);
              setPasswordSuccess(false);
            }}
            onSubmitEditing={handleChangePassword}
            placeholder="Nowe hasło"
            returnKeyType="done"
            secureTextEntry
            value={newPassword}
          />
          <ErrorMessage
            message={
              passwordFormError ??
              (changePassword.isError ? "Nie udało się zmienić hasła." : null)
            }
          />
          {passwordSuccess ? (
            <Text className="text-sm text-green-700">
              Hasło zostało zmienione.
            </Text>
          ) : null}
          <Button
            disabled={changePassword.isPending}
            onPress={handleChangePassword}
          >
            {changePassword.isPending ? "Zapisywanie..." : "Zmień hasło"}
          </Button>
        </View>

        <Button
          disabled={auth.logout.isPending}
          onPress={() => auth.logout.mutate()}
          variant="outline"
        >
          {auth.logout.isPending ? "Wylogowywanie..." : "Wyloguj"}
        </Button>
      </ScrollView>
    </Screen>
  );
}
