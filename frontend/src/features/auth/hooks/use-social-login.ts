import { useCallback, useEffect, useRef, useState } from "react";
import * as WebBrowser from "expo-web-browser";
import * as Google from "expo-auth-session/build/providers/Google";
import * as Facebook from "expo-auth-session/build/providers/Facebook";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Platform } from "react-native";
import { ENV } from "@core/config/env";
import { authService } from "@core/auth/auth.service";
import { authQueryKeys } from "../constants/auth-query-keys";

WebBrowser.maybeCompleteAuthSession();

const googleClientId =
  Platform.OS === "android"
    ? ENV.GOOGLE_ANDROID_CLIENT_ID
    : ENV.GOOGLE_WEB_CLIENT_ID || ENV.GOOGLE_CLIENT_ID;

const webRedirectUriOptions =
  Platform.OS === "web" ? { preferLocalhost: true } : {};

const webRedirectUri =
  Platform.OS === "web" && typeof window !== "undefined"
    ? window.location.origin
    : undefined;

/**
 * Obsługuje logowanie social przez Expo AuthSession i allauth provider_token.
 */
export function useSocialLogin() {
  const queryClient = useQueryClient();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const handledGoogleResponse = useRef<string | null>(null);
  const handledFacebookResponse = useRef<string | null>(null);

  const loginWithProviderToken = useMutation({
    mutationFn: authService.loginWithProviderToken,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: authQueryKeys.all });
    },
    onError: () => {
      setErrorMessage("Nie udało się zalogować przez zewnętrznego providera.");
    },
  });

  const [googleRequest, googleResponse, promptGoogle] =
    Google.useIdTokenAuthRequest(
      {
        clientId: googleClientId,
        webClientId: ENV.GOOGLE_WEB_CLIENT_ID,
        androidClientId: ENV.GOOGLE_ANDROID_CLIENT_ID,
        redirectUri: webRedirectUri,
        scopes: ["openid", "profile", "email"],
        selectAccount: true,
      },
      webRedirectUriOptions,
    );

  const [facebookRequest, facebookResponse, promptFacebook] =
    Facebook.useAuthRequest(
      {
        clientId: ENV.FACEBOOK_CLIENT_ID,
        webClientId: ENV.FACEBOOK_CLIENT_ID,
        androidClientId: ENV.FACEBOOK_CLIENT_ID,
        redirectUri: webRedirectUri,
        scopes: ["public_profile", "email"],
      },
      webRedirectUriOptions,
    );

  useEffect(() => {
    if (!__DEV__ || !googleRequest) return;

    console.info("[Auth] Google OAuth request", {
      platform: Platform.OS,
      clientId: googleRequest.clientId,
      redirectUri: googleRequest.redirectUri,
      responseType: googleRequest.responseType,
    });
  }, [googleRequest]);

  useEffect(() => {
    if (googleResponse?.type !== "success") return;
    if (handledGoogleResponse.current === googleResponse.url) return;

    handledGoogleResponse.current = googleResponse.url;

    const idToken =
      googleResponse.params.id_token ?? googleResponse.authentication?.idToken;

    if (!idToken) {
      setErrorMessage("Google nie zwrócił tokena tożsamości.");
      return;
    }

    setErrorMessage(null);
    loginWithProviderToken.mutate({
      provider: "google",
      clientId: googleClientId,
      idToken,
    });
  }, [googleResponse, loginWithProviderToken]);

  useEffect(() => {
    if (facebookResponse?.type !== "success") return;
    if (handledFacebookResponse.current === facebookResponse.url) return;

    handledFacebookResponse.current = facebookResponse.url;

    const accessToken =
      facebookResponse.params.access_token ??
      facebookResponse.authentication?.accessToken;

    if (!accessToken) {
      setErrorMessage("Facebook nie zwrócił tokena dostępu.");
      return;
    }

    setErrorMessage(null);
    loginWithProviderToken.mutate({
      provider: "facebook",
      clientId: ENV.FACEBOOK_CLIENT_ID,
      accessToken,
    });
  }, [facebookResponse, loginWithProviderToken]);

  const startGoogleLogin = useCallback(() => {
    if (!googleRequest || !googleClientId) {
      setErrorMessage("Brakuje konfiguracji Google OAuth.");
      return;
    }

    setErrorMessage(null);
    void promptGoogle();
  }, [googleRequest, promptGoogle]);

  const startFacebookLogin = useCallback(() => {
    if (!facebookRequest || !ENV.FACEBOOK_CLIENT_ID) {
      setErrorMessage("Brakuje konfiguracji Facebook OAuth.");
      return;
    }

    setErrorMessage(null);
    void promptFacebook();
  }, [facebookRequest, promptFacebook]);

  return {
    startGoogleLogin,
    startFacebookLogin,
    isGoogleReady: !!googleRequest && !!googleClientId,
    isFacebookReady: !!facebookRequest && !!ENV.FACEBOOK_CLIENT_ID,
    isPending: loginWithProviderToken.isPending,
    errorMessage,
  };
}
