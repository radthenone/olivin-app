"use client";

import Link from "next/link";
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
  AuthCodeField,
  AuthFormCard,
  AuthFormError,
  AuthSubmitButton,
} from "./auth-form-shell";
import { authRoutes } from "./auth-routes";
import {
  verifyEmailErrorKey,
  verifyEmailErrorsFromFailure,
} from "./signup-errors";

import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";

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
      <AuthFormCard
        description={t("verifyEmail.success")}
        title={t("verifyEmail.title")}
      >
        <Button asChild>
          <Link href={authRoutes.home(locale)}>
            {t("verifyEmail.backToHome")}
          </Link>
        </Button>
      </AuthFormCard>
    );
  }

  return (
    <AuthFormCard
      description={t("verifyEmail.description")}
      title={t("verifyEmail.title")}
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
            label={t("verifyEmail.code")}
            name="key"
          />

          <AuthFormError message={rootError} />

          <AuthSubmitButton
            isPending={isPending}
            label={t("verifyEmail.submit")}
            pendingLabel={t("verifyEmail.submitting")}
          />
        </form>
      </Form>
    </AuthFormCard>
  );
}
