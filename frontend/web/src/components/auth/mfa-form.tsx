"use client";

import Link from "next/link";
import type { Route } from "next";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { useForm } from "react-hook-form";

import {
  mapAllauthBodyToAuthState,
  useMfaAuthenticate,
  type MfaError,
} from "@olivin/features/auth";

import { mfaErrorsFromFailure } from "./mfa-errors";

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

type MfaFormValues = {
  code: string;
};

/**
 * Drugi składnik logowania na webie (#354).
 *
 * Allauth po poprawnym haśle zwraca flow `mfa_authenticate`, więc formularz
 * hasła przekazuje sterowanie tutaj. Poprawny kod kończy logowanie (sesja
 * odświeża się przez wspólny hook), a zły zostaje przy polu kodu. Gdy
 * oczekujące logowanie wygaśnie, `onExpired` zgłasza to rodzicowi, który
 * wraca do formularza, z którego logowanie się zaczęło (hasło albo kod).
 */
export function MfaForm({ onExpired }: { onExpired: () => void }) {
  const t = useTranslations("auth");
  const locale = useLocale();
  const { mutateAsync, isPending } = useMfaAuthenticate();
  const [isDone, setIsDone] = useState(false);
  const form = useForm<MfaFormValues>({ defaultValues: { code: "" } });

  const rootError = form.formState.errors.root?.message;

  function errorMessage(error: MfaError): string {
    if (error.code === "codeInvalid") {
      return t("errors.mfaCodeInvalid");
    }

    if (error.code === "tooManyAttempts") {
      return t("errors.tooManyAttempts");
    }

    return error.message ?? t("errors.mfaFailed");
  }

  function showErrors(errors: MfaError[]) {
    for (const error of errors) {
      form.setError(error.target === "code" ? "code" : "root", {
        type: "server",
        message: errorMessage(error),
      });
    }
  }

  async function onSubmit(values: MfaFormValues) {
    form.clearErrors();

    try {
      const response = await mutateAsync({ code: values.code });

      if (response.status === 200) {
        form.reset();
        setIsDone(true);
        return;
      }

      // 401 bez flow `mfa_authenticate` znaczy, że allauth porzucił oczekujące
      // logowanie — kolejne kody nic nie dadzą, trzeba wrócić do hasła.
      if (mapAllauthBodyToAuthState(response.data).status !== "mfa_required") {
        onExpired();
        return;
      }

      form.setError("code", {
        type: "server",
        message: t("errors.mfaCodeInvalid"),
      });
    } catch (error) {
      const mapped = mfaErrorsFromFailure(error);
      if (mapped) {
        showErrors(mapped);
        return;
      }

      form.setError("root", {
        type: "server",
        message: t("errors.mfaFailed"),
      });
    }
  }

  if (isDone) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <h1 className="text-2xl font-semibold text-neutral-900">
              {t("mfa.title")}
            </h1>
          </CardTitle>
          <CardDescription>{t("mfa.success")}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link href={`/${locale}` as Route}>{t("mfa.backToHome")}</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h1 className="text-2xl font-semibold text-neutral-900">
            {t("mfa.title")}
          </h1>
        </CardTitle>
        <CardDescription>{t("mfa.description")}</CardDescription>
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
              rules={{ required: t("errors.mfaCodeRequired") }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("mfa.code")}</FormLabel>
                  <FormControl>
                    <Input
                      autoComplete="one-time-code"
                      disabled={isPending}
                      inputMode="numeric"
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
              {isPending ? t("mfa.submitting") : t("mfa.submit")}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
