import type { PropsWithChildren, ReactNode } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Text,
  View,
} from "react-native";
import { cn } from "@core/styles/cn";

type AuthShellProps = PropsWithChildren<{
  title: string;
  subtitle: string;
  footer?: ReactNode;
  className?: string;
}>;

/**
 * Wspólny layout ekranów auth.
 *
 * Dlaczego istnieje:
 * login, rejestracja, MFA i reset hasła powinny mieć jeden rytm UI,
 * a różnice formularzy powinny mieszkać w samych ekranach.
 */
export function AuthShell({
  title,
  subtitle,
  footer,
  className,
  children,
}: AuthShellProps) {
  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      className="flex-1 bg-white"
      style={{ backgroundColor: "#ffffff" }}
    >
      <ScrollView
        contentContainerClassName="min-h-full justify-center px-5 py-10 web:mx-auto web:w-full web:max-w-md"
        style={{ backgroundColor: "#ffffff" }}
        keyboardShouldPersistTaps="handled"
      >
        <View className={cn("gap-7", className)}>
          <View className="gap-2">
            <Text className="text-3xl font-semibold text-neutral-950">
              {title}
            </Text>
            <Text className="text-base leading-6 text-neutral-600">
              {subtitle}
            </Text>
          </View>

          <View className="gap-4">{children}</View>

          {footer ? <View className="gap-3">{footer}</View> : null}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
