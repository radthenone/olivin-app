import type { PropsWithChildren } from "react";
import { Pressable, Text } from "react-native";
import { cn } from "@core/styles/cn";
import {
  buttonTextVariants,
  buttonVariants,
  type ButtonVariantProps,
} from "./button.variants";

type ButtonProps = PropsWithChildren<
  ButtonVariantProps & {
    onPress?: () => void;
    disabled?: boolean;
    className?: string;
    textClassName?: string;
  }
>;

/**
 * Podstawowy przycisk aplikacji.
 *
 * Dlaczego istnieje:
 * feature screens nie powinny ręcznie składać stylu przycisków.
 */
export function Button({
  children,
  onPress,
  disabled,
  variant,
  size,
  className,
  textClassName,
}: ButtonProps) {
  return (
    <Pressable
      disabled={disabled}
      onPress={onPress}
      className={cn(buttonVariants({ variant, size, disabled }), className)}
    >
      <Text
        className={cn(buttonTextVariants({ variant, size }), textClassName)}
      >
        {children}
      </Text>
    </Pressable>
  );
}
