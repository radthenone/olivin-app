"use client";

import Link from "next/link";
import type { Route } from "next";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { useVerifyEmail, type VerifyEmailError } from "@olivin/features/auth";
import {
  toVerifyEmailBody,
  verifyEmailFormSchema,
  type VerifyEmailFormValues,
} from "@olivin/schemas";

import {
  verifyEmailErrorKey,
  verifyEmailErrorsFromFailure,
} from "./signup-errors";

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
 * Potwierdzenie e-maila kodem z wiadomości (#351).
 *
 * Allauth przyjmuje kod jako `key`; po sukcesie sesja jest już zalogowana,
 * więc strona pokazuje potwierdzenie i prowadzi do sklepu.
 */
export function VerifyEmailForm() {
  const t = useTranslations("auth");
  const locale = useLocale();
  const verifyEmail = useVerifyEmail();
  const [isVerified, setIsVerified] = useState(false);
  const form = useForm<VerifyEmailFormValues>({ defaultValues: { key: "" } });
  const isPending = verifyEmail.isPending;

  const rootError = form.formState.errors.root?.message;

  function errorMessage(error: VerifyEmailError): string {
    const key = verifyEmailErrorKey(error);

    return key ? t(key) : (error.message ?? t("errors.verificationFailed"));
  }

  function showErrors(errors: VerifyEmailError[]) {
    for (const error of errors) {
      form.setError("root", { type: "server", message: errorMessage(error) });
    }
  }

  async function onSubmit(values: VerifyEmailFormValues) {
    form.clearErrors();

    const parsed = verifyEmailFormSchema.safeParse(values);
    if (!parsed.success) {
      form.setError("key", {
        type: "validation",
        message: t("errors.codeRequired"),
      });
      return;
    }

    try {
      const response = await verifyEmail.mutateAsync(
        toVerifyEmailBody(parsed.data),
      );

      if (response.status === 200) {
        form.reset();
        setIsVerified(true);
        return;
      }

      form.setError("root", {
        type: "server",
        message: t("errors.codeInvalid"),
      });
    } catch (error) {
      const mapped = verifyEmailErrorsFromFailure(error);
      if (mapped) {
        showErrors(mapped);
        return;
      }

      form.setError("root", {
        type: "server",
        message: t("errors.verificationFailed"),
      });
    }
  }

  if (isVerified) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <h1 className="text-2xl font-semibold text-neutral-900">
              {t("verifyEmail.title")}
            </h1>
          </CardTitle>
          <CardDescription>{t("verifyEmail.success")}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link href={`/${locale}` as Route}>
              {t("verifyEmail.backToHome")}
            </Link>
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
            {t("verifyEmail.title")}
          </h1>
        </CardTitle>
        <CardDescription>{t("verifyEmail.description")}</CardDescription>
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
                  <FormLabel>{t("verifyEmail.code")}</FormLabel>
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
                ? t("verifyEmail.submitting")
                : t("verifyEmail.submit")}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
