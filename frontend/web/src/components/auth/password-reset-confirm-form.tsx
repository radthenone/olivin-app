"use client";

import Link from "next/link";
import type { Route } from "next";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";

import {
  mapAllauthBodyToAuthState,
  useResetPassword,
  type PasswordResetError,
} from "@olivin/features/auth";
import {
  passwordResetConfirmFormSchema,
  toPasswordResetConfirmBody,
  type PasswordResetConfirmFormValues,
} from "@olivin/schemas";

import {
  isTooManyAttempts,
  passwordResetErrorsFromFailure,
  passwordResetValidationErrors,
} from "./password-reset-errors";

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
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";

/**
 * Ustawienie nowego hasła kodem z e-maila (#353, ADR 0038).
 *
 * Kod i nowe hasło idą jednym żądaniem. Gdy allauth loguje klienta po resecie
 * (200), wracamy do sklepu z gotową sesją. Gdy wymaga ponownego logowania
 * (401), prowadzimy na stronę logowania — adres nie niesie kodu ani tokenu.
 */
export function PasswordResetConfirmForm() {
  const t = useTranslations("auth");
  const locale = useLocale();
  const router = useRouter();
  const resetPassword = useResetPassword();
  const form = useForm<PasswordResetConfirmFormValues>({
    defaultValues: { key: "", password: "" },
  });
  const isPending = resetPassword.isPending;

  const rootError = form.formState.errors.root?.message;

  function errorMessage(error: PasswordResetError): string {
    if (error.code === "codeInvalid") return t("errors.codeInvalid");
    if (error.code === "passwordInvalid") return t("errors.passwordInvalid");
    if (error.code === "tooManyAttempts") return t("errors.tooManyAttempts");
    return error.message ?? t("errors.generic");
  }

  function showErrors(errors: PasswordResetError[]) {
    for (const error of errors) {
      if (error.target === "key" || error.target === "password") {
        form.setError(error.target, {
          type: "server",
          message: errorMessage(error),
        });
        continue;
      }

      form.setError("root", { type: "server", message: errorMessage(error) });
    }
  }

  async function onSubmit(values: PasswordResetConfirmFormValues) {
    form.clearErrors();

    const parsed = passwordResetConfirmFormSchema.safeParse(values);
    if (!parsed.success) {
      for (const { field, key } of passwordResetValidationErrors(
        parsed.error.issues,
      )) {
        if (field === "key" || field === "password") {
          form.setError(field, { type: "validation", message: t(key) });
        }
      }
      return;
    }

    try {
      const response = await resetPassword.mutateAsync(
        toPasswordResetConfirmBody(parsed.data),
      );
      const state = mapAllauthBodyToAuthState(response.data);

      form.reset();
      router.push(
        (state.status === "authenticated"
          ? `/${locale}`
          : `/${locale}/login`) as Route,
      );
    } catch (error) {
      if (isTooManyAttempts(error)) {
        form.setError("root", {
          type: "server",
          message: t("errors.tooManyAttempts"),
        });
        return;
      }

      const fieldErrors = passwordResetErrorsFromFailure(error);
      if (fieldErrors) {
        showErrors(fieldErrors);
        return;
      }

      form.setError("root", {
        type: "server",
        message: t("errors.generic"),
      });
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h1 className="text-2xl font-semibold text-neutral-900">
            {t("passwordReset.confirmTitle")}
          </h1>
        </CardTitle>
        <CardDescription>
          {t("passwordReset.confirmDescription")}
        </CardDescription>
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
              name="key"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("passwordReset.code")}</FormLabel>
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

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("passwordReset.password")}</FormLabel>
                  <FormControl>
                    <Input
                      autoComplete="new-password"
                      disabled={isPending}
                      type="password"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    {t("passwordReset.passwordHint")}
                  </FormDescription>
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
                ? t("passwordReset.confirmSubmitting")
                : t("passwordReset.confirmSubmit")}
            </Button>

            <Link
              className="text-center text-sm text-neutral-700 underline underline-offset-4"
              href={`/${locale}/login` as Route}
            >
              {t("passwordReset.backToLogin")}
            </Link>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
