import { useEffect, useState } from "react";
import { Text, View } from "react-native";
import { Link } from "expo-router";
import { ErrorMessage } from "@ui/feedback/ErrorMessage";
import { Button } from "@ui/primitives/Button";
import { TextField } from "@ui/primitives/TextField";
import { AuthShell } from "../components/AuthShell";
import {
  confirmLoginCodeSchema,
  requestLoginCodeSchema,
} from "../forms/login-by-code.schema";
import { useConfirmLoginCode } from "../hooks/use-confirm-login-code";
import { useRequestLoginCode } from "../hooks/use-request-login-code";

type LoginByCodeStep = "email" | "code";

const LOGIN_CODE_TTL_SECONDS = 180;
const LOGIN_CODE_RESEND_COOLDOWN_SECONDS = 30;

function formatCountdown(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}

/**
 * Ekran logowania jednorazowym kodem email.
 */
export function LoginByCodeScreen() {
  const requestLoginCode = useRequestLoginCode();
  const confirmLoginCode = useConfirmLoginCode();
  const [step, setStep] = useState<LoginByCodeStep>("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [codeTtlSeconds, setCodeTtlSeconds] = useState(0);
  const [resendCooldownSeconds, setResendCooldownSeconds] = useState(0);

  useEffect(() => {
    if (step !== "code") {
      return;
    }

    const intervalId = setInterval(() => {
      setCodeTtlSeconds((current) => Math.max(current - 1, 0));
      setResendCooldownSeconds((current) => Math.max(current - 1, 0));
    }, 1000);

    return () => {
      clearInterval(intervalId);
    };
  }, [step]);

  function startCodeTimers() {
    setCodeTtlSeconds(LOGIN_CODE_TTL_SECONDS);
    setResendCooldownSeconds(LOGIN_CODE_RESEND_COOLDOWN_SECONDS);
  }

  function handleRequestCode() {
    const parsed = requestLoginCodeSchema.safeParse({ email });

    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Sprawdź email.");
      return;
    }

    setFormError(null);
    requestLoginCode.mutate(parsed.data, {
      onSuccess: () => {
        setStep("code");
        setCode("");
        startCodeTimers();
      },
    });
  }

  function handleConfirmCode() {
    const parsed = confirmLoginCodeSchema.safeParse({ code });

    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Sprawdź kod.");
      return;
    }

    setFormError(null);
    confirmLoginCode.mutate(parsed.data);
  }

  const isPending = requestLoginCode.isPending || confirmLoginCode.isPending;
  const isCodeExpired = step === "code" && codeTtlSeconds === 0;
  const canResendCode =
    step === "code" && !isPending && resendCooldownSeconds === 0;

  return (
    <AuthShell
      title="Logowanie kodem"
      subtitle="Podaj email, a wyślemy jednorazowy kod do szybkiego logowania."
      footer={
        <Link href="/login">
          <Text className="text-center text-base text-neutral-950 underline">
            Wróć do logowania hasłem
          </Text>
        </Link>
      }
    >
      <TextField
        autoCapitalize="none"
        autoComplete="email"
        editable={!isPending && step === "email"}
        keyboardType="email-address"
        label="Email"
        onChangeText={(value) => {
          setEmail(value);
          setFormError(null);
        }}
        onSubmitEditing={handleRequestCode}
        placeholder="email@example.com"
        returnKeyType="done"
        value={email}
      />

      {step === "code" ? (
        <>
          <Text className="text-sm leading-5 text-emerald-700">
            Jeśli konto istnieje, kod logowania został wysłany.
          </Text>

          <View className="gap-2 rounded-md border border-neutral-200 bg-neutral-50 p-3">
            <Text className="text-sm font-medium text-neutral-950">
              {isCodeExpired
                ? "Kod wygasł. Wyślij nowy kod."
                : `Kod ważny jeszcze ${formatCountdown(codeTtlSeconds)}.`}
            </Text>
            <Text className="text-sm leading-5 text-neutral-600">
              Jeśli wiadomość nie dotarła, możesz poprosić o kolejny kod.
            </Text>
          </View>

          <TextField
            autoCapitalize="characters"
            editable={!isPending && !isCodeExpired}
            label="Kod logowania"
            onChangeText={(value) => {
              setCode(value);
              setFormError(null);
            }}
            onSubmitEditing={handleConfirmCode}
            placeholder="ABC123"
            returnKeyType="done"
            value={code}
          />

          <Button
            disabled={!canResendCode}
            onPress={handleRequestCode}
            variant="outline"
          >
            {requestLoginCode.isPending
              ? "Wysyłanie..."
              : resendCooldownSeconds > 0
                ? `Wyślij ponownie za ${formatCountdown(resendCooldownSeconds)}`
                : "Wyślij ponownie kod"}
          </Button>
        </>
      ) : null}

      <ErrorMessage
        message={
          formError ??
          (requestLoginCode.isError
            ? "Nie udało się wysłać kodu logowania."
            : null) ??
          (confirmLoginCode.isError
            ? "Nie udało się potwierdzić kodu logowania."
            : null)
        }
      />

      {step === "email" ? (
        <Button disabled={isPending} onPress={handleRequestCode}>
          {requestLoginCode.isPending ? "Wysyłanie..." : "Wyślij kod"}
        </Button>
      ) : (
        <Button
          disabled={isPending || isCodeExpired}
          onPress={handleConfirmCode}
        >
          {confirmLoginCode.isPending ? "Sprawdzanie..." : "Zaloguj kodem"}
        </Button>
      )}
    </AuthShell>
  );
}
