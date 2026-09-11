# shadcn/ui na web, React Native Reusables na mobile

shadcn/ui opiera się na DOM i nie działa w React Native, ale jego odpowiednik dla React Native — React Native Reusables — powiela te same nazwy komponentów, tę samą anatomię i tę samą filozofię kopiowania kodu do projektu. Obie biblioteki czytają tokeny z tego samego źródła, więc komponenty wyglądają jak rodzeństwo i pisze się je tak samo, mimo że to dwa osobne drzewa kodu.

## Considered Options

Rozważono pisanie własnych prymitywów od zera na obie platformy — odrzucone, bo prymitywy pod spodem obu bibliotek obsługują zarządzanie fokusem, nawigację klawiaturą i czytniki ekranu, czyli obszar, w którym ręczne implementacje zawodzą najczęściej i najdotkliwiej.

Rozważono Tamagui jako jeden uniwersalny system dla obu celów — odrzucone, bo wymagałby porzucenia NativeWind i przyjęcia własnego języka stylowania o istotnie mniejszej adopcji.
