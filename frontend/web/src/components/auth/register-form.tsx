"use client";

import Link from "next/link";
import type { Route } from "next";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";

import {
  mapAllauthBodyToAuthState,
  useRegister,
  type SignupError,
} from "@olivin/features/auth";
import {
  NO_SIGNUP_CONSENTS,
  PASSWORD_MIN_LENGTH,
  USERNAME_MAX_LENGTH,
  USERNAME_MIN_LENGTH,
  assertSignupBody,
  registerFormSchema,
  toSignupBody,
  type RegisterFormInput,
} from "@olivin/schemas";

import {
  registerErrorsFromFailure,
  registerValidationErrors,
  signupErrorKey,
} from "./signup-errors";
import { SignupConsents } from "./signup-consents";
import { ProviderButtons } from "./provider-buttons";

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

const DEFAULT_VALUES: RegisterFormInput = {
  email: "",
  username: "",
  password: "",
  passwordConfirm: "",
  ...NO_SIGNUP_CONSENTS,
};

type ValidationIssue = { path: readonly PropertyKey[]; message: string };

/**
 * Rejestracja e-mailem z wymaganymi zgodami (#351).
 *
 * Schemat `@olivin/schemas` jest jedynym źródłem reguł formularza, a błędy
 * backendu trafiają do pól przez `mapSignupErrors`. Po wysłaniu allauth
 * przechodzi do weryfikacji e-maila kodem, więc sukces prowadzi na osobną
 * stronę weryfikacji.
 */
export function RegisterForm() {
  const t = useTranslations("auth");
  const locale = useLocale();
  const router = useRouter();
  const register = useRegister();
  const form = useForm<RegisterFormInput>({ defaultValues: DEFAULT_VALUES });
  const isPending = register.isPending;

  const rootError = form.formState.errors.root?.message;

  function errorMessage(error: SignupError): string {
    const key = signupErrorKey(error);

    return key ? t(key) : (error.message ?? t("errors.registrationFailed"));
  }

  function showValidationIssues(issues: ValidationIssue[]) {
    for (const { field, key } of registerValidationErrors(issues)) {
      form.setError(field, { type: "validation", message: t(key) });
    }
  }

  function showErrors(errors: SignupError[]) {
    for (const error of errors) {
      form.setError(error.target === "form" ? "root" : error.target, {
        type: "server",
        message: errorMessage(error),
      });
    }
  }

  async function onSubmit(values: RegisterFormInput) {
    form.clearErrors();

    const parsed = registerFormSchema.safeParse(values);
    if (!parsed.success) {
      showValidationIssues(parsed.error.issues);
      return;
    }

    try {
      const body = assertSignupBody(toSignupBody(parsed.data));
      const response = await register.mutateAsync(body);
      const state = mapAllauthBodyToAuthState(response.data);

      if (state.status === "email_verification_required") {
        router.push(`/${locale}/register/verify` as Route);
        return;
      }

      if (state.status === "authenticated") {
        form.reset(DEFAULT_VALUES);
        router.push(`/${locale}` as Route);
        return;
      }

      form.setError("root", {
        type: "server",
        message: t("errors.registrationFailed"),
      });
    } catch (error) {
      // Backend odrzuca rejestrację błędami przy polach (np. zajęta nazwa),
      // więc pokazujemy je przy właściwych kontrolkach.
      const fieldErrors = registerErrorsFromFailure(error);
      if (fieldErrors) {
        showErrors(fieldErrors);
        return;
      }

      form.setError("root", {
        type: "server",
        message: t("errors.registrationFailed"),
      });
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h1 className="text-2xl font-semibold text-neutral-900">
            {t("register.title")}
          </h1>
        </CardTitle>
        <CardDescription>{t("register.description")}</CardDescription>
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
                  <FormLabel>{t("register.email")}</FormLabel>
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

            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("register.username")}</FormLabel>
                  <FormControl>
                    <Input
                      autoCapitalize="none"
                      autoComplete="username"
                      disabled={isPending}
                      maxLength={USERNAME_MAX_LENGTH}
                      minLength={USERNAME_MIN_LENGTH}
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    {t("register.usernameHint")}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("register.password")}</FormLabel>
                  <FormControl>
                    <Input
                      autoComplete="new-password"
                      disabled={isPending}
                      minLength={PASSWORD_MIN_LENGTH}
                      type="password"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    {t("register.passwordHint")}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="passwordConfirm"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("register.passwordConfirm")}</FormLabel>
                  <FormControl>
                    <Input
                      autoComplete="new-password"
                      disabled={isPending}
                      type="password"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <SignupConsents disabled={isPending} />

            {rootError && (
              <p className="text-sm text-destructive" role="alert">
                {rootError}
              </p>
            )}

            <Button disabled={isPending} type="submit">
              {isPending ? t("register.submitting") : t("register.submit")}
            </Button>

            <p className="text-sm text-neutral-700">
              {t("register.haveAccount")}{" "}
              <Link
                className="underline underline-offset-4"
                href={`/${locale}/login` as Route}
              >
                {t("register.loginLink")}
              </Link>
            </p>
          </form>
        </Form>

        <div className="mt-6">
          <ProviderButtons />
        </div>
      </CardContent>
    </Card>
  );
}
