import type { PropsWithChildren } from "react";

export default function Root({ children }: PropsWithChildren) {
  return (
    <html lang="pl">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#6366f1" />

        {/* SEO */}
        <meta name="description" content="Twój sklep internetowy" />
        <meta property="og:site_name" content="NazwaSklepu" />

        {/* Fonty */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />

        {/* Favicon */}
        <link rel="icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />

        {/* Tailwind / global CSS wstrzykuje Expo automatycznie */}
      </head>
      <body>
        {/* children = cała aplikacja Expo/React */}
        {children}
      </body>
    </html>
  );
}
