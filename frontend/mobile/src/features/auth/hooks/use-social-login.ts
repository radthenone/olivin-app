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

type SocialProvider = "google" | "facebook";

/**
 * Obsługuje logowanie social przez Expo AuthSession i allauth provider_token.
 */
export function useSocialLogin() {
  const queryClient = useQueryClient();
  const [startErrorMessage, setStartErrorMessage] = useState<string | null>(
    null,
  );
  const [activeProvider, setActiveProvider] = useState<SocialProvider | null>(
    null,
  );
  const handledGoogleResponse = useRef<string | null>(null);
  const handledFacebookResponse = useRef<string | null>(null);

  const {
    mutate: loginWithProviderToken,
    isPending,
    isError: isLoginError,
  } = useMutation({
    mutationFn: authService.loginWithProviderToken,
    onSuccess: async (state) => {
      // Nowe konto z Google/Facebook: 401 z flow `provider_signup` — stan od
      // razu w cache, żeby routing przeniósł na ekran zgód (#207).
      if (state.status === "provider_signup_required") {
        queryClient.setQueryData(authQueryKeys.session(), state);
      }
      await queryClient.invalidateQueries({ queryKey: authQueryKeys.all });
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

  const googleIdToken =
    googleResponse?.type === "success"
      ? (googleResponse.params.id_token ??
        googleResponse.authentication?.idToken)
      : undefined;
  const facebookAccessToken =
    facebookResponse?.type === "success"
      ? (facebookResponse.params.access_token ??
        facebookResponse.authentication?.accessToken)
      : undefined;

  useEffect(() => {
    if (googleResponse?.type !== "success") return;
    if (handledGoogleResponse.current === googleResponse.url) return;

    handledGoogleResponse.current = googleResponse.url;

    if (!googleIdToken) return;

    loginWithProviderToken({
      provider: "google",
      clientId: googleClientId,
      idToken: googleIdToken,
    });
  }, [googleIdToken, googleResponse, loginWithProviderToken]);

  useEffect(() => {
    if (facebookResponse?.type !== "success") return;
    if (handledFacebookResponse.current === facebookResponse.url) return;

    handledFacebookResponse.current = facebookResponse.url;

    if (!facebookAccessToken) return;

    loginWithProviderToken({
      provider: "facebook",
      clientId: ENV.FACEBOOK_CLIENT_ID,
      accessToken: facebookAccessToken,
    });
  }, [facebookAccessToken, facebookResponse, loginWithProviderToken]);

  const startGoogleLogin = useCallback(() => {
    if (!googleRequest || !googleClientId) {
      setStartErrorMessage("Brakuje konfiguracji Google OAuth.");
      return;
    }

    setStartErrorMessage(null);
    setActiveProvider("google");
    void promptGoogle();
  }, [googleRequest, promptGoogle]);

  const startFacebookLogin = useCallback(() => {
    if (!facebookRequest || !ENV.FACEBOOK_CLIENT_ID) {
      setStartErrorMessage("Brakuje konfiguracji Facebook OAuth.");
      return;
    }

    setStartErrorMessage(null);
    setActiveProvider("facebook");
    void promptFacebook();
  }, [facebookRequest, promptFacebook]);

  const providerTokenErrorMessage =
    activeProvider === "google" &&
    googleResponse?.type === "success" &&
    !googleIdToken
      ? "Google nie zwrócił tokena tożsamości."
      : activeProvider === "facebook" &&
          facebookResponse?.type === "success" &&
          !facebookAccessToken
        ? "Facebook nie zwrócił tokena dostępu."
        : null;

  const errorMessage =
    startErrorMessage ??
    providerTokenErrorMessage ??
    (isLoginError
      ? "Nie udało się zalogować przez zewnętrznego providera."
      : null);

  return {
    startGoogleLogin,
    startFacebookLogin,
    isGoogleReady: !!googleRequest && !!googleClientId,
    isFacebookReady: !!facebookRequest && !!ENV.FACEBOOK_CLIENT_ID,
    isPending,
    errorMessage,
  };
}
