"use client";

import type { Route } from "next";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";

import {
  mapAllauthBodyToAuthState,
  useProviderSignup,
  useProviderSignupInfo,
  type SignupError,
} from "@olivin/features/auth";
import {
  NO_SIGNUP_CONSENTS,
  USERNAME_MAX_LENGTH,
  USERNAME_MIN_LENGTH,
  assertProviderSignupBody,
  providerSignupFormSchema,
  toProviderSignupBody,
  type ProviderSignupFormInput,
} from "@olivin/schemas";

import { ProviderCallbackMessage } from "./provider-callback-message";
import { SignupConsents } from "./signup-consents";
import {
  registerErrorsFromFailure,
  registerValidationErrors,
  signupErrorKey,
  type RegisterField,
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
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";

const DEFAULT_VALUES: ProviderSignupFormInput = {
  username: "",
  ...NO_SIGNUP_CONSENTS,
};

const PROVIDER_FIELDS: ReadonlySet<string> = new Set<RegisterField>([
  "username",
  "consentTerms",
  "consentPrivacy",
  "consentMarketing",
]);

type ProviderField = Extract<
  RegisterField,
  "username" | "consentTerms" | "consentPrivacy" | "consentMarketing"
>;

/**
 * Dokończenie rejestracji po powrocie od Google/Facebook (#355).
 *
 * E-mail przychodzi od dostawcy i tylko go wyświetlamy. Nazwę użytkownika i
 * zgody zbiera ten sam fragment co przy rejestracji e-mailem, a reguły pilnuje
 * schemat `@olivin/schemas`.
 */
export function ProviderSignupForm() {
  const t = useTranslations("auth");
  const locale = useLocale();
  const router = useRouter();
  const info = useProviderSignupInfo();
  const providerSignup = useProviderSignup();
  const form = useForm<ProviderSignupFormInput>({
    defaultValues: DEFAULT_VALUES,
  });
  const isPending = providerSignup.isPending;

  const email =
    info.data?.status === 200
      ? info.data.data.data.email.find((item) => item.primary)?.email
      : undefined;
  const rootError = form.formState.errors.root?.message;

  function showValidationIssues(
    issues: { path: readonly PropertyKey[]; message: string }[],
  ) {
    for (const { field, key } of registerValidationErrors(issues)) {
      if (!PROVIDER_FIELDS.has(field)) continue;

      form.setError(field as ProviderField, {
        type: "validation",
        message: t(key),
      });
    }
  }

  function showErrors(errors: SignupError[]) {
    for (const error of errors) {
      const key = signupErrorKey(error);
      const message = key
        ? t(key)
        : (error.message ?? t("provider.signup.failed"));

      form.setError(error.target === "username" ? "username" : "root", {
        type: "server",
        message,
      });
    }
  }

  async function onSubmit(values: ProviderSignupFormInput) {
    form.clearErrors();

    if (!email) {
      form.setError("root", {
        type: "server",
        message: t("provider.signup.failed"),
      });
      return;
    }

    const parsed = providerSignupFormSchema.safeParse(values);
    if (!parsed.success) {
      showValidationIssues(parsed.error.issues);
      return;
    }

    try {
      const body = assertProviderSignupBody(
        toProviderSignupBody(email, parsed.data),
      );
      const response = await providerSignup.mutateAsync(body);

      if (mapAllauthBodyToAuthState(response.data).status === "authenticated") {
        form.reset(DEFAULT_VALUES);
        router.push(`/${locale}` as Route);
        return;
      }

      form.setError("root", {
        type: "server",
        message: t("provider.signup.failed"),
      });
    } catch (error) {
      // Nazwa zajęta albo odrzucona przez backend wraca przy polu, a reszta
      // dostaje ogólny komunikat.
      const fieldErrors = registerErrorsFromFailure(error);
      if (fieldErrors) {
        showErrors(fieldErrors);
        return;
      }

      form.setError("root", {
        type: "server",
        message: t("provider.signup.failed"),
      });
    }
  }

  if (info.isPending) {
    return null;
  }

  if (!email) {
    return <ProviderCallbackMessage message={t("provider.signup.failed")} />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h1 className="text-2xl font-semibold text-neutral-900">
            {t("provider.signup.title")}
          </h1>
        </CardTitle>
        <CardDescription>{t("provider.signup.description")}</CardDescription>
      </CardHeader>

      <CardContent>
        <div className="mb-4 flex flex-col gap-1">
          <p className="text-sm text-neutral-700">
            {t("provider.signup.email")}
          </p>
          <p className="font-medium text-neutral-900">{email}</p>
        </div>

        <Form {...form}>
          <form
            className="flex flex-col gap-4"
            noValidate
            onSubmit={form.handleSubmit(onSubmit)}
          >
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

            <SignupConsents disabled={isPending} />

            {rootError && (
              <p className="text-sm text-destructive" role="alert">
                {rootError}
              </p>
            )}

            <Button disabled={isPending} type="submit">
              {isPending
                ? t("provider.signup.submitting")
                : t("provider.signup.submit")}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
