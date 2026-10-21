/**
 * Klient allauth, z którym rozmawia web.
 *
 * Tryb `browser` trzyma sesję w ciasteczkach i wymaga CSRF. Aplikacja mobilna
 * używa `app` i nagłówka z tokenem sesji.
 */
export const AUTH_CLIENT = "browser" as const;
