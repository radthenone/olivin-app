.
├─ app/ # tylko routing + layouty (Expo Router)
│ ├─ \_layout.tsx # root layout (providers, theme, query, itp.)
│ ├─ (auth)/ # route group: bez wpływu na ścieżkę
│ │ ├─ \_layout.tsx # auth stack layout
│ │ ├─ sign-in.tsx
│ │ ├─ sign-up.tsx
│ │ └─ forgot-password.tsx
│ ├─ (tabs)/
│ │ ├─ \_layout.tsx # tabs layout
│ │ ├─ index.tsx # home tab
│ │ ├─ profile.tsx
│ │ └─ settings.tsx
│ ├─ (modals)/ # np. modalne flow
│ │ ├─ \_layout.tsx
│ │ └─ edit-profile.tsx
│ └─ +not-found.tsx
│
├─ src/
│ ├─ core/ # fundamenty aplikacji (bez “feature”)
│ │ ├─ env/ # config, baseURL, feature flags
│ │ ├─ theme/
│ │ │ ├─ tokens.ts # kolory, spacing, radius, typography
│ │ │ ├─ tailwind.ts # mapowanie tokenów na TW config (jeśli trzeba)
│ │ │ └─ ThemeProvider.tsx
│ │ ├─ ui/ # współdzielone komponenty UI (design system)
│ │ │ ├─ primitives/ # Button, Text, Input, Card...
│ │ │ ├─ layout/ # Stack, Spacer, Screen, Header...
│ │ │ └─ feedback/ # Toast, Loader, EmptyState...
│ │ ├─ navigation/ # helpery do routingu (opcjonalnie)
│ │ ├─ auth/
│ │ │ ├─ auth.store.ts # stan (Zustand/Redux/Context)
│ │ │ ├─ auth.service.ts # login/logout/refresh
│ │ │ ├─ auth.storage.ts # SecureStore wrapper
│ │ │ └─ auth.types.ts
│ │ ├─ api/
│ │ │ ├─ client.ts # fetch client + CSRF/session token
│ │ │ ├─ endpoints.ts # ścieżki endpointów
│ │ │ ├─ client.ts # generyczny client (get/post)
│ │ │ └─ api.types.ts
│ │ ├─ hooks/ # globalne hooki (useDebounce, useAppState...)
│ │ └─ utils/ # formatery, guards, helpers
│ │
│ ├─ features/ # “apps w appce” (każdy moduł osobno)
│ │ ├─ home/
│ │ │ ├─ screens/
│ │ │ ├─ components/
│ │ │ ├─ hooks/
│ │ │ ├─ home.api.ts # zapytania per feature (używa src/core/api)
│ │ │ └─ home.types.ts
│ │ ├─ profile/
│ │ └─ settings/
│ │
│ ├─ assets/ # fonty, ikony, obrazki
│ └─ test/ # testy unit/integration (jeśli robisz)
│
├─ tailwind.config.js
├─ app.json
└─ package.json
