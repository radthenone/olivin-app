import { useEffect, useState } from "react";
import { ScrollView, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { z } from "zod";
import { useAuthContext } from "@core/auth/auth.provider";
import { ApiError } from "@core/http/errors";
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

/**
 * Ekran ustawień konta użytkownika.
 *
 * Dlaczego istnieje:
 * zbiera dane sesji, profil oraz ustawienia bezpieczeństwa w jednym miejscu,
 * bez przenoszenia server state do lokalnego store.
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

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [profileFormError, setProfileFormError] = useState<string | null>(null);
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [email, setEmail] = useState("");
  const [emailFormError, setEmailFormError] = useState<string | null>(null);
  const [emailSuccess, setEmailSuccess] = useState(false);
  const [mfaCode, setMfaCode] = useState("");
  const [mfaFormError, setMfaFormError] = useState<string | null>(null);
  const [totpSetupSnapshot, setTotpSetupSnapshot] = useState<{
    secret?: string;
    totp_url?: string;
  } | null>(null);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordFormError, setPasswordFormError] = useState<string | null>(
    null,
  );
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  const displayName =
    profile.data?.fullName || auth.user?.display || auth.user?.email;

  useEffect(() => {
    if (!profile.data) return;

    setFirstName(profile.data.firstName ?? "");
    setLastName(profile.data.lastName ?? "");
    setPhoneNumber(profile.data.phoneNumber ?? "");
  }, [profile.data]);

  useEffect(() => {
    setEmail(auth.user?.email ?? "");
  }, [auth.user?.email]);

  useEffect(() => {
    if (totp.data?.status === "active") {
      setTotpSetupSnapshot(null);
      return;
    }

    if (
      totp.data?.status === "inactive" &&
      totp.data.setup &&
      !totpSetupSnapshot
    ) {
      setTotpSetupSnapshot({
        secret: totp.data.setup.secret,
        totp_url: totp.data.setup.totp_url,
      });
    }
  }, [totp.data, totpSetupSnapshot]);

  function handleSaveProfile() {
    const parsed = profileEditSchema.safeParse({
      firstName,
      lastName,
      phoneNumber,
    });

    if (!parsed.success) {
      setProfileFormError(
        parsed.error.issues[0]?.message ?? "Sprawdź dane profilu.",
      );
      return;
    }

    setProfileFormError(null);
    setProfileSuccess(false);
    saveProfile.mutate(parsed.data, {
      onSuccess: () => setProfileSuccess(true),
    });
  }

  function handleRequestEmailChange() {
    const parsed = emailChangeSchema.safeParse({ email });

    if (!parsed.success) {
      setEmailFormError(parsed.error.issues[0]?.message ?? "Sprawdź email.");
      return;
    }

    setEmailFormError(null);
    setEmailSuccess(false);
    requestEmailChange.mutate(parsed.data, {
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
        setTotpSetupSnapshot(null);
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
    totp.data?.status === "inactive"
      ? (totpSetupSnapshot ?? totp.data.setup)
      : null;

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

        <View className="gap-3">
          <Text className="text-lg font-semibold text-neutral-950">
            Edycja profilu
          </Text>
          <TextField
            editable={!saveProfile.isPending}
            label="Imię"
            onChangeText={(value) => {
              setFirstName(value);
              setProfileFormError(null);
              setProfileSuccess(false);
            }}
            value={firstName}
          />
          <TextField
            editable={!saveProfile.isPending}
            label="Nazwisko"
            onChangeText={(value) => {
              setLastName(value);
              setProfileFormError(null);
              setProfileSuccess(false);
            }}
            value={lastName}
          />
          <TextField
            editable={!saveProfile.isPending}
            keyboardType="phone-pad"
            label="Telefon"
            onChangeText={(value) => {
              setPhoneNumber(value);
              setProfileFormError(null);
              setProfileSuccess(false);
            }}
            onSubmitEditing={handleSaveProfile}
            placeholder="+48 123 456 789"
            returnKeyType="done"
            value={phoneNumber}
          />
          <ErrorMessage
            message={
              profileFormError ??
              (saveProfile.isError ? "Nie udało się zapisać profilu." : null)
            }
          />
          {profileSuccess ? (
            <Text className="text-sm text-green-700">
              Profil został zapisany.
            </Text>
          ) : null}
          <Button disabled={saveProfile.isPending} onPress={handleSaveProfile}>
            {saveProfile.isPending ? "Zapisywanie..." : "Zapisz profil"}
          </Button>
        </View>

        <View className="gap-3">
          <Text className="text-lg font-semibold text-neutral-950">
            Zmiana emaila
          </Text>
          <TextField
            autoCapitalize="none"
            autoComplete="email"
            editable={!requestEmailChange.isPending}
            keyboardType="email-address"
            label="Nowy email"
            onChangeText={(value) => {
              setEmail(value);
              setEmailFormError(null);
              setEmailSuccess(false);
            }}
            onSubmitEditing={handleRequestEmailChange}
            placeholder="email@example.com"
            returnKeyType="done"
            value={email}
          />
          <ErrorMessage
            message={
              emailFormError ??
              (requestEmailChange.isError
                ? "Nie udało się rozpocząć zmiany emaila."
                : null)
            }
          />
          {emailSuccess ? (
            <Text className="text-sm text-green-700">
              Wysłano wiadomość potwierdzającą zmianę emaila.
            </Text>
          ) : null}
          <Button
            disabled={requestEmailChange.isPending}
            onPress={handleRequestEmailChange}
          >
            {requestEmailChange.isPending ? "Wysyłanie..." : "Zmień email"}
          </Button>
        </View>

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
