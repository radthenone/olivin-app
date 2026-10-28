"use client";

import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useForm } from "react-hook-form";

import { useRequestLoginCode } from "@olivin/features/auth";
import {
  requestLoginCodeFormSchema,
  toRequestLoginCodeBody,
  type RequestLoginCodeFormValues,
} from "@olivin/schemas";

import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";

import {
  AuthFormCard,
  AuthFormError,
  AuthFormLink,
  AuthSubmitButton,
} from "./auth-form-shell";
import { authRoutes } from "./auth-routes";
import { isTooManyAttempts } from "./login-errors";

/**
 * Zamówienie jednorazowego kodu logowania (#352).
 *
 * Po przyjęciu adresu przez allauth przechodzimy na ekran wpisania kodu —
 * backend trzyma oczekujący etap w sesji, więc ekran kodu nie potrzebuje
 * adresu w adresie strony. Flaga `expired` oznacza powrót z ekranu MFA po
 * wygaśnięciu logowania (#409); komunikat pokazujemy raz, a adres zaraz
 * czyścimy, żeby odświeżenie go nie przywracało.
 */
export function LoginCodeRequestForm({
  expired = false,
}: {
  expired?: boolean;
}) {
  const t = useTranslations("auth");
  const locale = useLocale();
  const router = useRouter();
  const requestCode = useRequestLoginCode();
  const form = useForm<RequestLoginCodeFormValues>({
    defaultValues: { email: "" },
  });
  const isPending = requestCode.isPending;

  useEffect(() => {
    if (!expired) {
      return;
    }

    form.setError("root", {
      type: "server",
      message: t("errors.mfaExpired"),
    });
    router.replace(authRoutes.loginCode(locale));
  }, [expired, form, locale, router, t]);

  const rootError = form.formState.errors.root?.message;

  async function onSubmit(values: RequestLoginCodeFormValues) {
    form.clearErrors();

    const parsed = requestLoginCodeFormSchema.safeParse(values);
    if (!parsed.success) {
      const isEmpty = parsed.error.issues[0]?.message === "email_required";
      form.setError("email", {
        type: "validation",
        message: t(isEmpty ? "errors.emailRequired" : "errors.emailInvalid"),
      });
      return;
    }

    try {
      await requestCode.mutateAsync(toRequestLoginCodeBody(parsed.data));
      router.push(authRoutes.loginCodeConfirm(locale));
    } catch (error) {
      form.setError("root", {
        type: "server",
        message: isTooManyAttempts(error)
          ? t("errors.tooManyAttempts")
          : t("loginCode.requestFailed"),
      });
    }
  }

  return (
    <AuthFormCard
      description={t("loginCode.description")}
      title={t("loginCode.title")}
    >
      <Form {...form}>
        <form
          className="flex flex-col gap-4"
          noValidate
          onSubmit={form.handleSubmit(onSubmit)}
        >
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t("loginCode.email")}</FormLabel>
                <FormControl>
                  <Input
                    autoComplete="email"
                    disabled={isPending}
                    type="email"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <AuthFormError message={rootError} />

          <AuthSubmitButton
            isPending={isPending}
            label={t("loginCode.requestSubmit")}
            pendingLabel={t("loginCode.requestSubmitting")}
          />

          <AuthFormLink href={authRoutes.login(locale)}>
            {t("loginCode.backToPassword")}
          </AuthFormLink>
        </form>
      </Form>
    </AuthFormCard>
  );
}
