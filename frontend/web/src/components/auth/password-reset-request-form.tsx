"use client";

import Link from "next/link";
import type { Route } from "next";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useForm } from "react-hook-form";

import { useRequestPasswordReset } from "@olivin/features/auth";
import {
  passwordResetRequestFormSchema,
  toPasswordResetRequestBody,
  type PasswordResetRequestFormValues,
} from "@olivin/schemas";

import { authRoutes } from "./auth-routes";
import {
  passwordResetFailureKey,
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
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";

/**
 * Prośba o kod resetu hasła (#353, ADR 0038).
 *
 * Po przyjęciu adresu przez allauth przechodzimy na ekran wpisania kodu.
 * Oczekujący etap resetu trzyma sesja backendu, więc w adresie strony nie ma
 * ani adresu e-mail, ani kodu. `expired` oznacza powrót z ekranu ustawienia
 * hasła po 409: etap resetu przepadł, więc trzeba zamówić nowy kod (#421).
 */
export function PasswordResetRequestForm({
  expired = false,
}: {
  expired?: boolean;
}) {
  const t = useTranslations("auth");
  const locale = useLocale();
  const router = useRouter();
  const requestReset = useRequestPasswordReset();
  const form = useForm<PasswordResetRequestFormValues>({
    defaultValues: { email: "" },
  });
  const isPending = requestReset.isPending;

  useEffect(() => {
    if (!expired) {
      return;
    }

    form.setError("root", {
      type: "server",
      message: t("errors.codeExpired"),
    });
    router.replace(authRoutes.passwordReset(locale));
  }, [expired, form, locale, router, t]);

  const rootError = form.formState.errors.root?.message;

  async function onSubmit(values: PasswordResetRequestFormValues) {
    form.clearErrors();

    const parsed = passwordResetRequestFormSchema.safeParse(values);
    if (!parsed.success) {
      for (const { field, key } of passwordResetValidationErrors(
        parsed.error.issues,
      )) {
        if (field === "email") {
          form.setError("email", { type: "validation", message: t(key) });
        }
      }
      return;
    }

    try {
      await requestReset.mutateAsync(toPasswordResetRequestBody(parsed.data));
      router.push(authRoutes.passwordResetConfirm(locale));
    } catch (error) {
      const failure = passwordResetFailureKey(error);
      form.setError("root", {
        type: "server",
        message:
          failure === "errors.tooManyAttempts"
            ? t(failure)
            : t("passwordReset.requestFailed"),
      });
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h1 className="text-2xl font-semibold text-neutral-900">
            {t("passwordReset.title")}
          </h1>
        </CardTitle>
        <CardDescription>{t("passwordReset.description")}</CardDescription>
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
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("passwordReset.email")}</FormLabel>
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

            {rootError && (
              <p className="text-sm text-destructive" role="alert">
                {rootError}
              </p>
            )}

            <Button disabled={isPending} type="submit">
              {isPending
                ? t("passwordReset.requestSubmitting")
                : t("passwordReset.requestSubmit")}
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
