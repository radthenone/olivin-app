"use client";

import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { AuthResponseError, useConfirmLoginCode } from "@olivin/features/auth";
import {
  confirmLoginCodeFormSchema,
  toConfirmLoginCodeBody,
  type ConfirmLoginCodeFormValues,
} from "@olivin/schemas";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";

import { authRoutes } from "./auth-routes";
import { isTooManyAttempts } from "./login-errors";
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
      form.setError("root", {
        type: "server",
        message: isTooManyAttempts(error)
          ? t("errors.tooManyAttempts")
          : error instanceof AuthResponseError
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
    <Card>
      <CardHeader>
        <CardTitle>
          <h1 className="text-2xl font-semibold text-neutral-900">
            {t("loginCode.confirmTitle")}
          </h1>
        </CardTitle>
        <CardDescription>{t("loginCode.confirmDescription")}</CardDescription>
      </CardHeader>

      <CardContent>
        <Form {...form}>
          <form
            className="flex flex-col gap-4"
            noValidate
            onSubmit={form.handleSubmit(onSubmit)}
          >
            <FormField
              control={form.control}
              name="code"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("loginCode.code")}</FormLabel>
                  <FormControl>
                    <Input
                      autoComplete="one-time-code"
                      disabled={isPending}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {rootError && (
              <p className="text-sm text-destructive" role="alert">
                {rootError}
              </p>
            )}

            <Button disabled={isPending} type="submit">
              {isPending
                ? t("loginCode.confirmSubmitting")
                : t("loginCode.confirmSubmit")}
            </Button>

            <Link
              className="text-center text-sm text-neutral-700 underline underline-offset-4"
              href={authRoutes.login(locale)}
            >
              {t("loginCode.backToPassword")}
            </Link>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
