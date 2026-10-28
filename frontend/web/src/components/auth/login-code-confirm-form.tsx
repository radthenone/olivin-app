"use client";

import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { loginCodeErrorCode, useConfirmLoginCode } from "@olivin/features/auth";
import {
  confirmLoginCodeFormSchema,
  toConfirmLoginCodeBody,
  type ConfirmLoginCodeFormValues,
} from "@olivin/schemas";

import { Form } from "@/components/ui/form";

import {
  AuthCodeField,
  AuthFormCard,
  AuthFormError,
  AuthFormLink,
  AuthSubmitButton,
} from "./auth-form-shell";
import { authRoutes } from "./auth-routes";
import { MfaForm } from "./mfa-form";

/**
 * Wpisanie jednorazowego kodu logowania (#352).
 *
 * Kod potwierdza allauth; po sukcesie sesja jest już zalogowana, więc
 * przechodzimy do sklepu, a nagłówek pokazuje nazwę użytkownika. Gdy konto ma
 * MFA, poprawny kod dopiero otwiera drugi składnik (#409).
 */
export function LoginCodeConfirmForm() {
  const t = useTranslations("auth");
  const locale = useLocale();
  const router = useRouter();
  const confirmCode = useConfirmLoginCode();
  const [isMfaRequired, setIsMfaRequired] = useState(false);
  const form = useForm<ConfirmLoginCodeFormValues>({
    defaultValues: { code: "" },
  });
  const isPending = confirmCode.isPending;

  const rootError = form.formState.errors.root?.message;

  async function onSubmit(values: ConfirmLoginCodeFormValues) {
    form.clearErrors();

    const parsed = confirmLoginCodeFormSchema.safeParse(values);
    if (!parsed.success) {
      form.setError("code", {
        type: "validation",
        message: t("errors.codeRequired"),
      });
      return;
    }

    try {
      const state = await confirmCode.mutateAsync(
        toConfirmLoginCodeBody(parsed.data),
      );

      if (state.status === "authenticated") {
        form.reset();
        router.push(authRoutes.home(locale));
        return;
      }

      // Poprawny kod przy koncie z MFA otwiera drugi składnik — to nie jest
      // zły kod, więc nie pokazujemy błędu przy polu.
      if (state.status === "mfa_required") {
        setIsMfaRequired(true);
        return;
      }

      form.setError("root", {
        type: "server",
        message: t("errors.codeInvalid"),
      });
    } catch (error) {
      const code = loginCodeErrorCode(error);

      // Etap potwierdzenia przepadł (limit prób albo wygasły kod), więc
      // kolejne kody nic nie dadzą — wracamy do zamówienia nowego.
      if (code === "codeExpired") {
        router.push(authRoutes.loginCodeExpired(locale, "code"));
        return;
      }

      form.setError("root", {
        type: "server",
        message:
          code === "tooManyAttempts"
            ? t("errors.tooManyAttempts")
            : code === "codeInvalid"
              ? t("errors.codeInvalid")
              : t("errors.generic"),
      });
    }
  }

  // Wygaśnięcie oczekującego logowania oznacza, że kod też przepadł — wracamy
  // na początek logowania kodem, żeby klient mógł zamówić nowy.
  function onMfaExpired() {
    router.push(authRoutes.loginCodeExpired(locale));
  }

  if (isMfaRequired) {
    return <MfaForm onExpired={onMfaExpired} />;
  }

  return (
    <AuthFormCard
      description={t("loginCode.confirmDescription")}
      title={t("loginCode.confirmTitle")}
    >
      <Form {...form}>
        <form
          className="flex flex-col gap-4"
          noValidate
          onSubmit={form.handleSubmit(onSubmit)}
        >
          <AuthCodeField
            control={form.control}
            disabled={isPending}
            label={t("loginCode.code")}
            name="code"
          />

          <AuthFormError message={rootError} />

          <AuthSubmitButton
            isPending={isPending}
            label={t("loginCode.confirmSubmit")}
            pendingLabel={t("loginCode.confirmSubmitting")}
          />

          <AuthFormLink href={authRoutes.login(locale)}>
            {t("loginCode.backToPassword")}
          </AuthFormLink>
        </form>
      </Form>
    </AuthFormCard>
  );
}
