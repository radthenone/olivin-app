# Graph Report - frontend  (2026-09-22)

## Corpus Check
- 446 files · ~375,740 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 7, .css 2, .lock 1)

## Summary
- 2636 nodes · 4412 edges · 190 communities (161 shown, 29 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Auth Account API Client
- Addresses API Client
- Addresses Zod Schemas
- 2FA API Client
- Profiles API Client
- Mobile Auth Forms
- Mobile Dependencies A
- Account Email API Client
- Password Reset API Client
- WebAuthn Login API Client
- Mobile Dependencies B
- Account WebAuthn API Client
- Social Providers API Client
- Orval Config & Env Loading
- Phone API Client
- Auth Provider & Layout
- Profiles Zod Schemas
- Signup Schema Types
- Account Services (Address/Profile)
- Consents API Client
- Login-by-Code API Client
- WebAuthn Signup API Client
- Product Schema Types
- Collections API Client
- Account Settings Screen
- 2FA Auth API Client
- API Package Manifest
- Account Providers API Client
- Auth Account Zod Schemas
- Categories API Client
- Current Session API Client
- Auth Meta Types
- Authenticator Code Types
- Products API Client
- Authenticator List Types
- Authenticated Response Types
- API Transport Core
- Consents & Password Zod
- Auth Config Types
- WebAuthn Login Zod
- Platform & CSRF
- Env Config & Logger
- HTTP Client & Logging
- Category Query Params
- Mobile Auth Service
- Health API & Web Home
- Account Email Zod
- 2FA Zod Schemas
- Turborepo Pipeline
- Mobile TS Config
- Web Dependencies A
- Mobile Screen Layout
- Account WebAuthn Zod
- Auth Mutator & Config
- Tokens API Client
- Money Package
- Schemas Package
- Product Filter Params
- Password API Client
- WebAuthn Add Types
- Change Password Types
- Mobile Transport & Web Layout
- Root Workspace Manifest
- Design Tokens Package
- Address Types
- OAuth Client Types
- Provider Account Types
- Web TS Config
- Mobile Dependencies C
- Mobile Dependencies D
- Base TS Config
- Products Zod
- Platform Component Factory
- WebAuthn Signup Zod
- Account Configuration Types
- Web Dependencies B
- Web Dependencies C
- Design Tokens Index
- Gemstone Enums
- Password Reset Zod
- Providers Zod
- Access/Refresh Token Types
- WebAuthn Body Types
- API Errors & Web HTTP
- Config Package
- Metro Bundler Config
- Auth Types & Mapper
- App Mutator (Addresses)
- Categories Zod
- 2FA Auth Zod
- Login-by-Code Zod
- API TS Config
- Login-by-Code Screen
- TOTP QR Code (Web)
- Collections Zod
- Profile Page Types
- Account Providers Zod
- Email Verification Types
- Phone Number Types
- Tokens CSS Generator
- Phone Zod
- Web Dependencies D
- Health Check Types
- Current Session Zod
- Conflict Response Types
- Login Code Types
- Error Response Types
- TOTP Not Found Types
- login-by-code.schema (forms)
- tailwind.config (mobile)
- Endpoint Hook: addresses #110
- Endpoint Hook: profiles #111
- Endpoint Hook: profiles #112
- Endpoint Hook: account-2fa #113
- Endpoint Hook: account-2fa #114
- Endpoint Hook: account-2fa #115
- Endpoint Hook: account-email #116
- Endpoint Hook: account-webauthn #117
- Endpoint Hook: authentication-account #118
- Endpoint Hook: authentication-providers #119
- Endpoint Hook: authentication-webauthn-login #120
- Endpoint Hook: authentication-webauthn-login #121
- Endpoint Hook: authentication-webauthn-login #122
- Endpoint Hook: authentication-webauthn-signup #123
- tsconfig (money)
- tsconfig (schemas)
- PasswordResetRequestScreen (screens)
- MfaVerifyScreen (screens)
- RegisterScreen (screens)
- PasswordResetConfirmScreen (screens)
- VerifyEmailScreen (screens)
- qrcode-terminal.d (types)
- Endpoint Hook: profiles #133
- Endpoint Hook: profiles #134
- Endpoint Hook: profiles #135
- Endpoint Hook: profiles #136
- Endpoint Hook: profiles #137
- consentDocument (schemas)
- Endpoint Hook: account-2fa #139
- Endpoint Hook: account-2fa #140
- Endpoint Hook: account-2fa #141
- Endpoint Hook: account-email #142
- Endpoint Hook: account-email #143
- Endpoint Hook: account-email #144
- Endpoint Hook: account-email #145
- Endpoint Hook: account-webauthn #146
- Endpoint Hook: account-webauthn #147
- Endpoint Hook: account-webauthn #148
- Endpoint Hook: authentication-account #149
- Endpoint Hook: authentication-account #150
- Endpoint Hook: authentication-account #151
- Endpoint Hook: authentication-account #152
- Endpoint Hook: authentication-account #153
- Endpoint Hook: authentication-account #154
- Endpoint Hook: authentication-account #155
- Endpoint Hook: authentication-login-by-code #156
- Endpoint Hook: authentication-login-by-code #157
- Endpoint Hook: authentication-login-by-code #158
- Endpoint Hook: authentication-providers #159
- Endpoint Hook: authentication-providers #160
- Endpoint Hook: authentication-providers #161
- Endpoint Hook: authentication-webauthn-login #162
- Endpoint Hook: authentication-webauthn-login #163
- Endpoint Hook: authentication-webauthn-login #164
- Endpoint Hook: authentication-webauthn-signup #165
- Endpoint Hook: authentication-webauthn-signup #166
- forbiddenResponse (schemas)
- getAllauthClientV1AccountAuthenticatorsWebauthnParams (schemas)
- notFoundResponse (schemas)
- tooManyRequestsResponse (schemas)
- verifyEmail (schemas)
- verifyPhone (schemas)
- index.d (tokens)
- +native-intent (app)
- TotpQrCode.native (TotpQrCode)
- next.config (web)
- package (web)
- session-token.storage.web (auth)
- routes (navigation)
- customersProfileListParams (schemas)
- markPrimaryEmailBody (schemas)
- postcss.config (web)

## God Nodes (most connected - your core abstractions)
1. `authInstance()` - 71 edges
2. `appInstance()` - 32 edges
3. `react-native` - 24 edges
4. `StatusOK` - 23 edges
5. `AuthenticationResponse` - 18 edges
6. `ErrorType` - 17 edges
7. `expo-router` - 16 edges
8. `ErrorResponse` - 16 edges
9. `AccountSettingsScreen()` - 15 edges
10. `BodyType` - 15 edges

## Surprising Connections (you probably didn't know these)
- `HomeRoute()` --calls--> `useAuthContext()`  [EXTRACTED]
  mobile/app/(app)/home.tsx → mobile/src/core/auth/auth.provider.tsx
- `configureMobileApi()` --calls--> `configureApi()`  [EXTRACTED]
  mobile/src/core/api/transport.ts → packages/api/src/transport.ts
- `HomePage()` --calls--> `useHealthRetrieve()`  [EXTRACTED]
  web/app/page.tsx → packages/api/generated/apps/health/health.ts
- `webRequest()` --calls--> `ApiError`  [EXTRACTED]
  web/src/lib/http.ts → packages/api/src/errors.ts
- `configureWebApi()` --calls--> `configureApi()`  [EXTRACTED]
  web/src/lib/api-transport.ts → packages/api/src/transport.ts

## Import Cycles
- None detected.

## Communities (190 total, 29 thin omitted)

### Community 0 - "Auth Account API Client"
Cohesion: 0.02
Nodes (80): GetAllauthClientV1AuthEmailVerifyQueryError, GetAllauthClientV1AuthEmailVerifyQueryResult, getAllauthClientV1AuthEmailVerifyResponse, getAllauthClientV1AuthEmailVerifyResponse200, getAllauthClientV1AuthEmailVerifyResponse400, getAllauthClientV1AuthEmailVerifyResponse409, getAllauthClientV1AuthEmailVerifyResponseError, getAllauthClientV1AuthEmailVerifyResponseSuccess (+72 more)

### Community 1 - "Addresses API Client"
Cohesion: 0.03
Nodes (72): customersAddressesCreate(), CustomersAddressesCreateMutationBody, CustomersAddressesCreateMutationError, CustomersAddressesCreateMutationResult, customersAddressesCreateResponse, customersAddressesCreateResponse201, customersAddressesCreateResponseSuccess, CustomersAddressesDestroyMutationError (+64 more)

### Community 2 - "Addresses Zod Schemas"
Cohesion: 0.03
Nodes (60): CustomersAddressesCreateBody, customersAddressesCreateBodyCityMax, customersAddressesCreateBodyPostalCodeMax, customersAddressesCreateBodyStateMax, customersAddressesCreateBodyStreet2Max, customersAddressesCreateBodyStreetMax, CustomersAddressesDestroyParams, CustomersAddressesListQueryParams (+52 more)

### Community 3 - "2FA API Client"
Cohesion: 0.04
Nodes (54): DeleteAllauthClientV1AccountAuthenticatorsTotpMutationError, DeleteAllauthClientV1AccountAuthenticatorsTotpMutationResult, deleteAllauthClientV1AccountAuthenticatorsTotpResponse, deleteAllauthClientV1AccountAuthenticatorsTotpResponse200, deleteAllauthClientV1AccountAuthenticatorsTotpResponse401, deleteAllauthClientV1AccountAuthenticatorsTotpResponseError, deleteAllauthClientV1AccountAuthenticatorsTotpResponseSuccess, GetAllauthClientV1AccountAuthenticatorsQueryError (+46 more)

### Community 4 - "Profiles API Client"
Cohesion: 0.04
Nodes (53): CustomersProfileChangeRolePartialUpdateMutationBody, CustomersProfileChangeRolePartialUpdateMutationError, CustomersProfileChangeRolePartialUpdateMutationResult, customersProfileChangeRolePartialUpdateResponse, customersProfileChangeRolePartialUpdateResponse200, customersProfileChangeRolePartialUpdateResponse403, customersProfileChangeRolePartialUpdateResponse404, customersProfileChangeRolePartialUpdateResponseError (+45 more)

### Community 5 - "Mobile Auth Forms"
Cohesion: 0.12
Nodes (32): PlatformValues, cn(), profileRequiredSchema, AuthShell(), AuthShellProps, LoginFormValues, loginSchema, MfaFormValues (+24 more)

### Community 6 - "Mobile Dependencies A"
Cohesion: 0.04
Nodes (49): dotenv, eslint, @olivin/api, @olivin/config, @olivin/tokens, react, react-dom, tailwindcss (+41 more)

### Community 7 - "Account Email API Client"
Cohesion: 0.04
Nodes (46): DeleteAllauthClientV1AccountEmailMutationBody, DeleteAllauthClientV1AccountEmailMutationError, DeleteAllauthClientV1AccountEmailMutationResult, deleteAllauthClientV1AccountEmailResponse, deleteAllauthClientV1AccountEmailResponse200, deleteAllauthClientV1AccountEmailResponse400, deleteAllauthClientV1AccountEmailResponseError, deleteAllauthClientV1AccountEmailResponseSuccess (+38 more)

### Community 8 - "Password Reset API Client"
Cohesion: 0.05
Nodes (45): getAllauthClientV1AuthPasswordReset(), GetAllauthClientV1AuthPasswordResetQueryError, GetAllauthClientV1AuthPasswordResetQueryResult, getAllauthClientV1AuthPasswordResetResponse, getAllauthClientV1AuthPasswordResetResponse200, getAllauthClientV1AuthPasswordResetResponse400, getAllauthClientV1AuthPasswordResetResponse409, getAllauthClientV1AuthPasswordResetResponseError (+37 more)

### Community 9 - "WebAuthn Login API Client"
Cohesion: 0.04
Nodes (44): GetAllauthClientV1AuthWebauthnAuthenticateQueryError, GetAllauthClientV1AuthWebauthnAuthenticateQueryResult, getAllauthClientV1AuthWebauthnAuthenticateResponse, getAllauthClientV1AuthWebauthnAuthenticateResponse200, getAllauthClientV1AuthWebauthnAuthenticateResponseSuccess, GetAllauthClientV1AuthWebauthnLoginQueryError, GetAllauthClientV1AuthWebauthnLoginQueryResult, getAllauthClientV1AuthWebauthnLoginResponse (+36 more)

### Community 10 - "Mobile Dependencies B"
Cohesion: 0.05
Nodes (44): dependencies, class-variance-authority, clsx, dotenv, dotenv-expand, expo, expo-auth-session, expo-constants (+36 more)

### Community 11 - "Account WebAuthn API Client"
Cohesion: 0.05
Nodes (42): DeleteAllauthClientV1AccountAuthenticatorsWebauthnMutationBody, DeleteAllauthClientV1AccountAuthenticatorsWebauthnMutationError, DeleteAllauthClientV1AccountAuthenticatorsWebauthnMutationResult, deleteAllauthClientV1AccountAuthenticatorsWebauthnResponse, deleteAllauthClientV1AccountAuthenticatorsWebauthnResponse200, deleteAllauthClientV1AccountAuthenticatorsWebauthnResponse401, deleteAllauthClientV1AccountAuthenticatorsWebauthnResponseError, deleteAllauthClientV1AccountAuthenticatorsWebauthnResponseSuccess (+34 more)

### Community 12 - "Social Providers API Client"
Cohesion: 0.05
Nodes (41): GetAllauthClientV1AuthProviderSignupQueryError, GetAllauthClientV1AuthProviderSignupQueryResult, getAllauthClientV1AuthProviderSignupResponse, getAllauthClientV1AuthProviderSignupResponse200, getAllauthClientV1AuthProviderSignupResponse409, getAllauthClientV1AuthProviderSignupResponseError, getAllauthClientV1AuthProviderSignupResponseSuccess, PostAllauthBrowserV1AuthProviderRedirectMutationBody (+33 more)

### Community 13 - "Orval Config & Env Loading"
Cohesion: 0.07
Nodes (27): { loadEnv }, { defineConfig }, expoConfig, path, {
  sharedIgnores,
  platformExtensions,
}, base, ALLAUTH_SCHEMA_URL, ALLAUTH_TAGS (+19 more)

### Community 14 - "Phone API Client"
Cohesion: 0.07
Nodes (33): getAllauthClientV1AccountPhone(), GetAllauthClientV1AccountPhoneQueryError, GetAllauthClientV1AccountPhoneQueryResult, getAllauthClientV1AccountPhoneResponse, getAllauthClientV1AccountPhoneResponse200, getAllauthClientV1AccountPhoneResponse401, getAllauthClientV1AccountPhoneResponseError, getAllauthClientV1AccountPhoneResponseSuccess (+25 more)

### Community 15 - "Auth Provider & Layout"
Cohesion: 0.09
Nodes (22): AppLayout(), AuthLayout(), IndexRoute(), RootNavigator(), AuthContext, AuthContextValue, AuthProvider(), useAuthContext() (+14 more)

### Community 16 - "Profiles Zod Schemas"
Cohesion: 0.06
Nodes (33): CustomersProfileChangeRolePartialUpdateBody, customersProfileChangeRolePartialUpdateBodyFirstNameMax, customersProfileChangeRolePartialUpdateBodyLastNameMax, CustomersProfileChangeRolePartialUpdateParams, CustomersProfileChangeRolePartialUpdateResponse, customersProfileChangeRolePartialUpdateResponseFirstNameMax, customersProfileChangeRolePartialUpdateResponseLastNameMax, CustomersProfileCreateBody (+25 more)

### Community 17 - "Signup Schema Types"
Cohesion: 0.10
Nodes (17): BaseSignup, Email, EmailAddress, EmailAddressesResponse, EmailBody, Login, LoginBody, PasskeySignup (+9 more)

### Community 18 - "Account Services (Address/Profile)"
Cohesion: 0.15
Nodes (9): accountQueryKeys, AddressCreateInput, addressService, AddressUpdateInput, ProfileEditableData, ProfileRequiredData, profileService, AuthResponseLike (+1 more)

### Community 19 - "Consents API Client"
Cohesion: 0.08
Nodes (30): consentsCreate(), ConsentsCreateMutationBody, ConsentsCreateMutationError, ConsentsCreateMutationResult, consentsCreateResponse, consentsCreateResponse201, consentsCreateResponseSuccess, consentsDocumentsList() (+22 more)

### Community 20 - "Login-by-Code API Client"
Cohesion: 0.06
Nodes (31): PostAllauthClientV1AuthCodeConfirmMutationBody, PostAllauthClientV1AuthCodeConfirmMutationError, PostAllauthClientV1AuthCodeConfirmMutationResult, postAllauthClientV1AuthCodeConfirmResponse, postAllauthClientV1AuthCodeConfirmResponse200, postAllauthClientV1AuthCodeConfirmResponse400, postAllauthClientV1AuthCodeConfirmResponse401, postAllauthClientV1AuthCodeConfirmResponse409 (+23 more)

### Community 21 - "WebAuthn Signup API Client"
Cohesion: 0.06
Nodes (31): GetAllauthClientV1AuthWebauthnSignupQueryError, GetAllauthClientV1AuthWebauthnSignupQueryResult, getAllauthClientV1AuthWebauthnSignupResponse, getAllauthClientV1AuthWebauthnSignupResponse200, getAllauthClientV1AuthWebauthnSignupResponse409, getAllauthClientV1AuthWebauthnSignupResponseError, getAllauthClientV1AuthWebauthnSignupResponseSuccess, PostAllauthClientV1AuthWebauthnSignupMutationBody (+23 more)

### Community 22 - "Product Schema Types"
Cohesion: 0.15
Nodes (18): ADR-0009, ADR-0013, FinenessEnum, LengthEnum, MaterialEnum, MetalColorEnum, Money, PaginatedProductListList (+10 more)

### Community 23 - "Collections API Client"
Cohesion: 0.09
Nodes (27): collectionsList(), CollectionsListQueryError, CollectionsListQueryResult, collectionsListResponse, collectionsListResponse200, collectionsListResponseSuccess, collectionsRetrieve(), CollectionsRetrieveQueryError (+19 more)

### Community 24 - "Account Settings Screen"
Cohesion: 0.10
Nodes (18): m_projects_olivin_app_frontend_mobile_src_features_account_components_totpqrcode_totpqrcode, mobile_src_features_account_components_totpqrcode_index_totpqrcode, ChangePasswordFormValues, changePasswordSchema, ProfileEditFormValues, profileEditSchema, SetupMfaFormValues, setupMfaSchema (+10 more)

### Community 25 - "2FA Auth API Client"
Cohesion: 0.08
Nodes (28): getPostAllauthClientV1Auth2faAuthenticateMutationOptions(), getPostAllauthClientV1Auth2faAuthenticateUrl(), getPostAllauthClientV1Auth2faReauthenticateMutationOptions(), getPostAllauthClientV1Auth2faReauthenticateUrl(), postAllauthClientV1Auth2faAuthenticate(), PostAllauthClientV1Auth2faAuthenticateMutationBody, PostAllauthClientV1Auth2faAuthenticateMutationError, PostAllauthClientV1Auth2faAuthenticateMutationResult (+20 more)

### Community 26 - "API Package Manifest"
Cohesion: 0.07
Nodes (28): dependencies, @tanstack/react-query, zod, description, devDependencies, dotenv, @olivin/config, orval (+20 more)

### Community 27 - "Account Providers API Client"
Cohesion: 0.09
Nodes (27): deleteAllauthClientV1AccountProviders(), DeleteAllauthClientV1AccountProvidersMutationBody, DeleteAllauthClientV1AccountProvidersMutationError, DeleteAllauthClientV1AccountProvidersMutationResult, deleteAllauthClientV1AccountProvidersResponse, deleteAllauthClientV1AccountProvidersResponse200, deleteAllauthClientV1AccountProvidersResponse400, deleteAllauthClientV1AccountProvidersResponseError (+19 more)

### Community 28 - "Auth Account Zod Schemas"
Cohesion: 0.07
Nodes (27): GetAllauthClientV1AuthEmailVerifyHeader, GetAllauthClientV1AuthEmailVerifyParams, GetAllauthClientV1AuthEmailVerifyResponse, PostAllauthClientV1AuthEmailVerifyBody, PostAllauthClientV1AuthEmailVerifyHeader, PostAllauthClientV1AuthEmailVerifyParams, PostAllauthClientV1AuthEmailVerifyResendHeader, PostAllauthClientV1AuthEmailVerifyResendParams (+19 more)

### Community 29 - "Categories API Client"
Cohesion: 0.10
Nodes (25): categoriesList(), CategoriesListQueryError, CategoriesListQueryResult, categoriesListResponse, categoriesListResponse200, categoriesListResponseSuccess, categoriesRetrieve(), CategoriesRetrieveQueryError (+17 more)

### Community 30 - "Current Session API Client"
Cohesion: 0.09
Nodes (26): deleteAllauthClientV1AuthSession(), DeleteAllauthClientV1AuthSessionMutationError, DeleteAllauthClientV1AuthSessionMutationResult, deleteAllauthClientV1AuthSessionResponse, deleteAllauthClientV1AuthSessionResponse401, deleteAllauthClientV1AuthSessionResponseError, getAllauthClientV1AuthSession(), GetAllauthClientV1AuthSessionQueryError (+18 more)

### Community 31 - "Auth Meta Types"
Cohesion: 0.14
Nodes (14): AuthenticatedMeta, AuthenticationMeta, AuthenticationOrReauthenticationResponse, AuthenticationResponse, AuthenticationResponseData, AuthenticationResponseStatus, BaseAuthenticationMeta, ReauthenticationRequiredResponse (+6 more)

### Community 32 - "Authenticator Code Types"
Cohesion: 0.12
Nodes (13): AuthenticatorCode, EmailVerificationKeyParameter, EndSessions, EndSessionsBody, MFAAuthenticate, MFAAuthenticateBody, MFATrust, MFATrustBody (+5 more)

### Community 33 - "Products API Client"
Cohesion: 0.10
Nodes (25): getProductsListQueryKey(), getProductsListQueryOptions(), getProductsListUrl(), getProductsRetrieveQueryKey(), getProductsRetrieveQueryOptions(), getProductsRetrieveUrl(), productsList(), ProductsListQueryError (+17 more)

### Community 34 - "Authenticator List Types"
Cohesion: 0.13
Nodes (13): AuthenticatorList, AuthenticatorsResponse, BaseAuthenticator, OptionalTimestamp, RecoveryCodesAuthenticator, RecoveryCodesAuthenticatorType, Session, SessionsResponse (+5 more)

### Community 35 - "Authenticated Response Types"
Cohesion: 0.16
Nodes (12): Authenticated, AuthenticatedByCodeResponse, AuthenticatedByPasswordAnd2FAResponse, AuthenticatedByPasswordResponse, AuthenticatedResponse, AuthenticationMethod, AuthenticatorType, Flow (+4 more)

### Community 36 - "API Transport Core"
Cohesion: 0.18
Nodes (17): buildRequestBody(), createRequest(), normalizeMethod(), buildUrl(), isPlainObject(), ApiErrorResponse, ApiFetcher, ApiTransport (+9 more)

### Community 37 - "Consents & Password Zod"
Cohesion: 0.10
Nodes (15): adultDateOfBirthSchema, ProfileRequiredFormValues, RegisterFormValues, ConsentsCreateBody, ConsentsDocumentsListResponse, ConsentsDocumentsListResponseItem, HealthRetrieveResponse, PostAllauthClientV1AccountPasswordChangeBody (+7 more)

### Community 38 - "Auth Config Types"
Cohesion: 0.14
Nodes (12): ConfigurationResponse, ConfigurationResponseData, PasswordResetInfoResponse, PasswordResetInfoResponseData, StatusOK, StatusOKResponse, WebAuthnCreationOptionsResponseResponse, WebAuthnCredentialCreationOptions (+4 more)

### Community 39 - "WebAuthn Login Zod"
Cohesion: 0.09
Nodes (21): GetAllauthClientV1AuthWebauthnAuthenticateHeader, GetAllauthClientV1AuthWebauthnAuthenticateParams, GetAllauthClientV1AuthWebauthnAuthenticateResponse, GetAllauthClientV1AuthWebauthnLoginHeader, GetAllauthClientV1AuthWebauthnLoginParams, GetAllauthClientV1AuthWebauthnLoginResponse, GetAllauthClientV1AuthWebauthnReauthenticateHeader, GetAllauthClientV1AuthWebauthnReauthenticateParams (+13 more)

### Community 40 - "Platform & CSRF"
Cohesion: 0.19
Nodes (14): ensureCsrfCookie(), getCookie(), getCsrfTokenFromCookie(), sessionTokenStorage, ENDPOINTS, mobile_src_core_config_platform_index_allauthclient, mobile_src_core_config_platform_index_isnative, allauthClient (+6 more)

### Community 41 - "Env Config & Logger"
Cohesion: 0.15
Nodes (12): sessionTokenStorage, alignWebLoopbackHost(), buildEnv(), ENV, normalizeUrl(), ExtraSchema, mobile_src_core_config_env_index_env, mobile_src_core_config_platform_index_isandroid (+4 more)

### Community 42 - "HTTP Client & Logging"
Cohesion: 0.21
Nodes (17): httpClient, httpRequest(), isAcceptedStatus(), compactArrayForLog(), compactForLog(), compactObjectForLog(), getDurationMs(), logError() (+9 more)

### Community 43 - "Category Query Params"
Cohesion: 0.14
Nodes (10): CategoriesListLang, CategoriesListParams, CategoriesRetrieveLang, CategoriesRetrieveParams, CollectionsListLang, CollectionsListParams, CollectionsRetrieveLang, CollectionsRetrieveParams (+2 more)

### Community 44 - "Mobile Auth Service"
Cohesion: 0.31
Nodes (5): AuthResponseLike, authService, SocialProviderTokenInput, authQueryKeys, ref_tanstack_react_query

### Community 45 - "Health API & Web Home"
Cohesion: 0.14
Nodes (16): getHealthRetrieveQueryKey(), getHealthRetrieveQueryOptions(), getHealthRetrieveUrl(), healthRetrieve(), HealthRetrieveQueryError, HealthRetrieveQueryResult, healthRetrieveResponse, healthRetrieveResponse200 (+8 more)

### Community 46 - "Account Email Zod"
Cohesion: 0.10
Nodes (19): DeleteAllauthClientV1AccountEmailBody, DeleteAllauthClientV1AccountEmailHeader, DeleteAllauthClientV1AccountEmailParams, DeleteAllauthClientV1AccountEmailResponse, GetAllauthClientV1AccountEmailHeader, GetAllauthClientV1AccountEmailParams, GetAllauthClientV1AccountEmailResponse, PatchAllauthClientV1AccountEmailBody (+11 more)

### Community 47 - "2FA Zod Schemas"
Cohesion: 0.11
Nodes (18): DeleteAllauthClientV1AccountAuthenticatorsTotpHeader, DeleteAllauthClientV1AccountAuthenticatorsTotpParams, DeleteAllauthClientV1AccountAuthenticatorsTotpResponse, GetAllauthClientV1AccountAuthenticatorsHeader, GetAllauthClientV1AccountAuthenticatorsParams, GetAllauthClientV1AccountAuthenticatorsRecoveryCodesHeader, GetAllauthClientV1AccountAuthenticatorsRecoveryCodesParams, GetAllauthClientV1AccountAuthenticatorsRecoveryCodesResponse (+10 more)

### Community 48 - "Turborepo Pipeline"
Cohesion: 0.11
Nodes (18): dependsOn, outputs, cache, persistent, cache, dependsOn, cache, $schema (+10 more)

### Community 49 - "Mobile TS Config"
Cohesion: 0.11
Nodes (17): compilerOptions, moduleSuffixes, paths, exclude, extends, include, @olivin/config/tsconfig/base.json, @app (+9 more)

### Community 50 - "Web Dependencies A"
Cohesion: 0.11
Nodes (17): @tailwindcss/postcss, @types/node, @types/react-dom, eslint, @olivin/api, @olivin/config, @olivin/tokens, react (+9 more)

### Community 51 - "Mobile Screen Layout"
Cohesion: 0.17
Nodes (9): HomeRoute(), useCurrentProfile(), useSaveRequiredProfile(), ProfileCompletionScreen(), useProfile(), ProfileScreen(), mobile_src_ui_layout_screen_index_screen, Screen() (+1 more)

### Community 52 - "Account WebAuthn Zod"
Cohesion: 0.12
Nodes (16): DeleteAllauthClientV1AccountAuthenticatorsWebauthnBody, DeleteAllauthClientV1AccountAuthenticatorsWebauthnHeader, DeleteAllauthClientV1AccountAuthenticatorsWebauthnParams, DeleteAllauthClientV1AccountAuthenticatorsWebauthnResponse, GetAllauthClientV1AccountAuthenticatorsWebauthnHeader, GetAllauthClientV1AccountAuthenticatorsWebauthnParams, GetAllauthClientV1AccountAuthenticatorsWebauthnQueryParams, GetAllauthClientV1AccountAuthenticatorsWebauthnResponse (+8 more)

### Community 53 - "Auth Mutator & Config"
Cohesion: 0.18
Nodes (15): getAllauthClientV1Config(), GetAllauthClientV1ConfigQueryError, GetAllauthClientV1ConfigQueryResult, getAllauthClientV1ConfigResponse, getAllauthClientV1ConfigResponse200, getAllauthClientV1ConfigResponseSuccess, getGetAllauthClientV1ConfigQueryKey(), getGetAllauthClientV1ConfigQueryOptions() (+7 more)

### Community 54 - "Tokens API Client"
Cohesion: 0.14
Nodes (16): packages_api_generated_auth_schemas_index_errorresponse, packages_api_generated_auth_schemas_index_refreshtokenbody, packages_api_generated_auth_schemas_index_refreshtokenresponse, getPostAllauthAppV1TokensRefreshMutationOptions(), getPostAllauthAppV1TokensRefreshUrl(), postAllauthAppV1TokensRefresh(), PostAllauthAppV1TokensRefreshMutationBody, PostAllauthAppV1TokensRefreshMutationError (+8 more)

### Community 55 - "Money Package"
Cohesion: 0.12
Nodes (16): description, devDependencies, @olivin/config, typescript, @olivin/config, typescript, main, name (+8 more)

### Community 56 - "Schemas Package"
Cohesion: 0.12
Nodes (16): description, devDependencies, @olivin/config, typescript, @olivin/config, typescript, main, name (+8 more)

### Community 57 - "Product Filter Params"
Cohesion: 0.18
Nodes (8): ProductsListFineness, ProductsListLang, ProductsListLength, ProductsListMaterial, ProductsListMetalColor, ProductsListParams, ProductsListSize, ProductsListStone

### Community 58 - "Password API Client"
Cohesion: 0.15
Nodes (15): getPostAllauthClientV1AccountPasswordChangeMutationOptions(), getPostAllauthClientV1AccountPasswordChangeUrl(), postAllauthClientV1AccountPasswordChange(), PostAllauthClientV1AccountPasswordChangeMutationBody, PostAllauthClientV1AccountPasswordChangeMutationError, PostAllauthClientV1AccountPasswordChangeMutationResult, postAllauthClientV1AccountPasswordChangeResponse, postAllauthClientV1AccountPasswordChangeResponse400 (+7 more)

### Community 59 - "WebAuthn Add Types"
Cohesion: 0.18
Nodes (8): AddWebAuthnAuthenticatorResponse, AddWebAuthnAuthenticatorResponseMeta, AuthenticatorID, DeleteWebAuthnBody, UpdateWebAuthnBody, WebAuthnAuthenticator, WebAuthnAuthenticatorResponse, WebAuthnAuthenticatorType

### Community 60 - "Change Password Types"
Cohesion: 0.20
Nodes (8): ChangePasswordBody, Password, Reauthenticate, ReauthenticateBody, ResetPassword, ResetPasswordBody, Signup, SignupBody

### Community 61 - "Mobile Transport & Web Layout"
Cohesion: 0.20
Nodes (10): configureMobileApi(), HTTP_METHODS, toConfig(), toHttpMethod(), handleAllauthSessionLifecycle(), configureApi(), web_app_globals, metadata (+2 more)

### Community 62 - "Root Workspace Manifest"
Cohesion: 0.13
Nodes (14): devDependencies, turbo, name, packageManager, private, scripts, build, format (+6 more)

### Community 63 - "Design Tokens Package"
Cohesion: 0.13
Nodes (14): description, devDependencies, @olivin/config, files, @olivin/config, main, name, prettier (+6 more)

### Community 64 - "Address Types"
Cohesion: 0.26
Nodes (7): Address, AddressCountry, BlankEnum, CountryEnum, PaginatedAddressList, PatchedAddress, PatchedAddressCountry

### Community 65 - "OAuth Client Types"
Cohesion: 0.30
Nodes (6): ClientID, Process, ProviderID, ProviderRedirect, ProviderToken, ProviderTokenToken

### Community 66 - "Provider Account Types"
Cohesion: 0.25
Nodes (6): Provider, ProviderAccount, ProviderAccountID, ProviderFlowsItem, ProviderSignupResponse, ProviderSignupResponseData

### Community 67 - "Web TS Config"
Cohesion: 0.14
Nodes (13): compilerOptions, allowJs, incremental, jsx, lib, moduleSuffixes, paths, plugins (+5 more)

### Community 68 - "Mobile Dependencies C"
Cohesion: 0.15
Nodes (13): devDependencies, ajv, babel-plugin-module-resolver, babel-plugin-transform-inline-environment-variables, eslint, eslint-config-expo, eslint-import-resolver-babel-module, @olivin/config (+5 more)

### Community 69 - "Mobile Dependencies D"
Cohesion: 0.15
Nodes (13): scripts, android, format, format:check, ios, lint, lint:fix, prebuild:android (+5 more)

### Community 70 - "Base TS Config"
Cohesion: 0.15
Nodes (12): compilerOptions, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, module, moduleResolution, noEmit, resolveJsonModule (+4 more)

### Community 71 - "Products Zod"
Cohesion: 0.17
Nodes (11): ProductsListQueryParams, ProductsListResponse, productsListResponseResultsItemCheapestVariantOneGemstonesItemCaratRegExp, productsListResponseResultsItemCheapestVariantOneMetalWeightGramsRegExp, productsListResponseResultsItemCheapestVariantOneVatRateRegExp, ProductsRetrieveParams, ProductsRetrieveQueryParams, ProductsRetrieveResponse (+3 more)

### Community 72 - "Platform Component Factory"
Cohesion: 0.25
Nodes (6): mobile_src_core_config_platform_index_selectplatform, selectPlatform(), createPlatformComponent(), PlatformComponentMap, PlatformNodeMap, platformRender()

### Community 73 - "WebAuthn Signup Zod"
Cohesion: 0.18
Nodes (10): GetAllauthClientV1AuthWebauthnSignupHeader, GetAllauthClientV1AuthWebauthnSignupParams, GetAllauthClientV1AuthWebauthnSignupResponse, PostAllauthClientV1AuthWebauthnSignupBody, PostAllauthClientV1AuthWebauthnSignupHeader, PostAllauthClientV1AuthWebauthnSignupParams, PutAllauthClientV1AuthWebauthnSignupBody, PutAllauthClientV1AuthWebauthnSignupHeader (+2 more)

### Community 74 - "Account Configuration Types"
Cohesion: 0.31
Nodes (5): AccountConfiguration, AccountConfigurationLoginMethodsItem, ProviderList, SocialAccountConfiguration, UserSessionsConfiguration

### Community 75 - "Web Dependencies B"
Cohesion: 0.18
Nodes (11): devDependencies, eslint, eslint-config-next, @olivin/config, @playwright/test, tailwindcss, @tailwindcss/postcss, @types/node (+3 more)

### Community 76 - "Web Dependencies C"
Cohesion: 0.18
Nodes (11): scripts, build, dev, e2e, format, format:check, lint, lint:fix (+3 more)

### Community 77 - "Design Tokens Index"
Cohesion: 0.20
Nodes (9): ADR-0005, borderRadius, boxShadow, colors, fontFamily, fontSize, fontWeight, screens (+1 more)

### Community 78 - "Gemstone Enums"
Cohesion: 0.38
Nodes (5): ClarityEnum, ColourEnum, CutEnum, Gemstone, StoneEnum

### Community 79 - "Password Reset Zod"
Cohesion: 0.20
Nodes (9): GetAllauthClientV1AuthPasswordResetHeader, GetAllauthClientV1AuthPasswordResetParams, GetAllauthClientV1AuthPasswordResetResponse, PostAllauthClientV1AuthPasswordRequestBody, PostAllauthClientV1AuthPasswordRequestParams, PostAllauthClientV1AuthPasswordRequestResponse, PostAllauthClientV1AuthPasswordResetBody, PostAllauthClientV1AuthPasswordResetParams (+1 more)

### Community 80 - "Providers Zod"
Cohesion: 0.20
Nodes (9): GetAllauthClientV1AuthProviderSignupParams, GetAllauthClientV1AuthProviderSignupResponse, PostAllauthClientV1AuthProviderSignupBody, PostAllauthClientV1AuthProviderSignupParams, PostAllauthClientV1AuthProviderSignupResponse, PostAllauthClientV1AuthProviderTokenBody, PostAllauthClientV1AuthProviderTokenHeader, PostAllauthClientV1AuthProviderTokenParams (+1 more)

### Community 81 - "Access/Refresh Token Types"
Cohesion: 0.29
Nodes (5): AccessToken, RefreshToken, RefreshTokenBody, RefreshTokenResponse, RefreshTokenResponseData

### Community 82 - "WebAuthn Body Types"
Cohesion: 0.29
Nodes (5): AddWebAuthnAuthenticatorBody, AuthenticateWebAuthnBody, LoginWebAuthnBody, ReauthenticateWebAuthnBody, WebAuthnCredential

### Community 83 - "API Errors & Web HTTP"
Cohesion: 0.29
Nodes (5): ApiError, baseUrl(), readBody(), resolve(), webRequest()

### Community 84 - "Config Package"
Cohesion: 0.20
Nodes (9): description, files, name, prettier, private, scripts, format, format:check (+1 more)

### Community 85 - "Metro Bundler Config"
Cohesion: 0.25
Nodes (8): config, escape(), excluded, { getDefaultConfig }, path, { withNativeWind }, workspaceRoot, expo

### Community 86 - "Auth Types & Mapper"
Cohesion: 0.36
Nodes (7): hasFlow(), mapAllauthBodyToAuthState(), AllauthBody, AllauthUser, AuthFlow, AuthState, isAllauthBody()

### Community 87 - "App Mutator (Addresses)"
Cohesion: 0.22
Nodes (9): customersAddressesDestroy(), customersAddressesUpdate(), getCustomersAddressesDestroyMutationOptions(), getCustomersAddressesDestroyUrl(), getCustomersAddressesUpdateMutationOptions(), getCustomersAddressesUpdateUrl(), useCustomersAddressesDestroy(), useCustomersAddressesUpdate() (+1 more)

### Community 88 - "Categories Zod"
Cohesion: 0.22
Nodes (8): CategoriesListQueryParams, CategoriesListResponse, CategoriesListResponseItem, categoriesListResponseSlugRegExp, CategoriesRetrieveParams, CategoriesRetrieveQueryParams, CategoriesRetrieveResponse, categoriesRetrieveResponseSlugRegExp

### Community 89 - "2FA Auth Zod"
Cohesion: 0.22
Nodes (8): PostAllauthClientV1Auth2faAuthenticateBody, PostAllauthClientV1Auth2faAuthenticateHeader, PostAllauthClientV1Auth2faAuthenticateParams, PostAllauthClientV1Auth2faAuthenticateResponse, PostAllauthClientV1Auth2faReauthenticateBody, PostAllauthClientV1Auth2faReauthenticateHeader, PostAllauthClientV1Auth2faReauthenticateParams, PostAllauthClientV1Auth2faReauthenticateResponse

### Community 90 - "Login-by-Code Zod"
Cohesion: 0.22
Nodes (8): PostAllauthClientV1AuthCodeConfirmBody, PostAllauthClientV1AuthCodeConfirmParams, PostAllauthClientV1AuthCodeConfirmResponse, PostAllauthClientV1AuthCodeRequestBody, PostAllauthClientV1AuthCodeRequestParams, PostAllauthClientV1AuthCodeResendHeader, PostAllauthClientV1AuthCodeResendParams, PostAllauthClientV1AuthCodeResendResponse

### Community 91 - "API TS Config"
Cohesion: 0.22
Nodes (8): compilerOptions, jsx, lib, types, exclude, extends, include, @olivin/config/tsconfig/base.json

### Community 92 - "Login-by-Code Screen"
Cohesion: 0.29
Nodes (6): useConfirmLoginCode(), useRequestLoginCode(), formatCountdown(), LoginByCodeScreen(), handleRequestCode(), startCodeTimers()

### Community 93 - "TOTP QR Code (Web)"
Cohesion: 0.32
Nodes (7): createQrModules(), QRCode, QRCodeConstructor, QRCodeInstance, QRErrorCorrectLevel, TotpQrCode(), TotpQrCodeProps

### Community 94 - "Collections Zod"
Cohesion: 0.25
Nodes (7): CollectionsListQueryParams, CollectionsListResponse, collectionsListResponseResultsItemSlugRegExp, CollectionsRetrieveParams, CollectionsRetrieveQueryParams, CollectionsRetrieveResponse, collectionsRetrieveResponseSlugRegExp

### Community 95 - "Profile Page Types"
Cohesion: 0.46
Nodes (4): PaginatedProfileList, PatchedProfile, Profile, RoleEnum

### Community 96 - "Account Providers Zod"
Cohesion: 0.25
Nodes (7): DeleteAllauthClientV1AccountProvidersBody, DeleteAllauthClientV1AccountProvidersHeader, DeleteAllauthClientV1AccountProvidersParams, DeleteAllauthClientV1AccountProvidersResponse, GetAllauthClientV1AccountProvidersHeader, GetAllauthClientV1AccountProvidersParams, GetAllauthClientV1AccountProvidersResponse

### Community 97 - "Email Verification Types"
Cohesion: 0.43
Nodes (4): EmailVerificationInfo, EmailVerificationInfoData, EmailVerificationInfoMeta, EmailVerificationInfoResponse

### Community 98 - "Phone Number Types"
Cohesion: 0.46
Nodes (4): PhoneNumber, PhoneNumberChangeResponse, PhoneNumbersResponse, StatusAccepted

### Community 99 - "Tokens CSS Generator"
Cohesion: 0.25
Nodes (7): ref_node_fs, ref_node_path, ref_node_url, contents, here, lines, outputPath

### Community 100 - "Phone Zod"
Cohesion: 0.29
Nodes (6): GetAllauthClientV1AccountPhoneHeader, GetAllauthClientV1AccountPhoneParams, GetAllauthClientV1AccountPhoneResponse, PostAllauthClientV1AccountPhoneBody, PostAllauthClientV1AccountPhoneHeader, PostAllauthClientV1AccountPhoneParams

### Community 101 - "Web Dependencies D"
Cohesion: 0.29
Nodes (7): dependencies, next, @olivin/api, @olivin/tokens, react, react-dom, @tanstack/react-query

### Community 102 - "Health Check Types"
Cohesion: 0.60
Nodes (3): HealthCheckResponse, HealthCheckServices, StatusEnum

### Community 103 - "Current Session Zod"
Cohesion: 0.33
Nodes (5): DeleteAllauthClientV1AuthSessionHeader, DeleteAllauthClientV1AuthSessionParams, GetAllauthClientV1AuthSessionHeader, GetAllauthClientV1AuthSessionParams, GetAllauthClientV1AuthSessionResponse

### Community 104 - "Conflict Response Types"
Cohesion: 0.53
Nodes (3): AddAuthenticatorConflictResponse, ConflictResponse, ConflictResponseStatus

### Community 105 - "Login Code Types"
Cohesion: 0.53
Nodes (3): Code, ConfirmLoginCode, ConfirmLoginCodeBody

### Community 106 - "Error Response Types"
Cohesion: 0.60
Nodes (3): ErrorResponse, ErrorResponseErrorsItem, ErrorResponseStatus

### Community 107 - "TOTP Not Found Types"
Cohesion: 0.47
Nodes (3): TOTPAuthenticatorNotFoundResponse, TOTPAuthenticatorNotFoundResponseMeta, TOTPAuthenticatorNotFoundResponseStatus

### Community 108 - "login-by-code.schema (forms)"
Cohesion: 0.40
Nodes (4): ConfirmLoginCodeFormValues, confirmLoginCodeSchema, RequestLoginCodeFormValues, requestLoginCodeSchema

### Community 109 - "tailwind.config (mobile)"
Cohesion: 0.40
Nodes (3): nativewind, tokens, nativewind

### Community 110 - "Endpoint Hook: addresses #110"
Cohesion: 0.40
Nodes (5): customersAddressesRetrieve(), getCustomersAddressesRetrieveQueryKey(), getCustomersAddressesRetrieveQueryOptions(), getCustomersAddressesRetrieveUrl(), useCustomersAddressesRetrieve()

### Community 111 - "Endpoint Hook: profiles #111"
Cohesion: 0.40
Nodes (5): customersProfileList(), getCustomersProfileListQueryKey(), getCustomersProfileListQueryOptions(), getCustomersProfileListUrl(), useCustomersProfileList()

### Community 112 - "Endpoint Hook: profiles #112"
Cohesion: 0.40
Nodes (5): customersProfileRetrieve(), getCustomersProfileRetrieveQueryKey(), getCustomersProfileRetrieveQueryOptions(), getCustomersProfileRetrieveUrl(), useCustomersProfileRetrieve()

### Community 113 - "Endpoint Hook: account-2fa #113"
Cohesion: 0.40
Nodes (5): getAllauthClientV1AccountAuthenticators(), getGetAllauthClientV1AccountAuthenticatorsQueryKey(), getGetAllauthClientV1AccountAuthenticatorsQueryOptions(), getGetAllauthClientV1AccountAuthenticatorsUrl(), useGetAllauthClientV1AccountAuthenticators()

### Community 114 - "Endpoint Hook: account-2fa #114"
Cohesion: 0.40
Nodes (5): getAllauthClientV1AccountAuthenticatorsRecoveryCodes(), getGetAllauthClientV1AccountAuthenticatorsRecoveryCodesQueryKey(), getGetAllauthClientV1AccountAuthenticatorsRecoveryCodesQueryOptions(), getGetAllauthClientV1AccountAuthenticatorsRecoveryCodesUrl(), useGetAllauthClientV1AccountAuthenticatorsRecoveryCodes()

### Community 115 - "Endpoint Hook: account-2fa #115"
Cohesion: 0.40
Nodes (5): getAllauthClientV1AccountAuthenticatorsTotp(), getGetAllauthClientV1AccountAuthenticatorsTotpQueryKey(), getGetAllauthClientV1AccountAuthenticatorsTotpQueryOptions(), getGetAllauthClientV1AccountAuthenticatorsTotpUrl(), useGetAllauthClientV1AccountAuthenticatorsTotp()

### Community 116 - "Endpoint Hook: account-email #116"
Cohesion: 0.40
Nodes (5): getAllauthClientV1AccountEmail(), getGetAllauthClientV1AccountEmailQueryKey(), getGetAllauthClientV1AccountEmailQueryOptions(), getGetAllauthClientV1AccountEmailUrl(), useGetAllauthClientV1AccountEmail()

### Community 117 - "Endpoint Hook: account-webauthn #117"
Cohesion: 0.40
Nodes (5): getAllauthClientV1AccountAuthenticatorsWebauthn(), getGetAllauthClientV1AccountAuthenticatorsWebauthnQueryKey(), getGetAllauthClientV1AccountAuthenticatorsWebauthnQueryOptions(), getGetAllauthClientV1AccountAuthenticatorsWebauthnUrl(), useGetAllauthClientV1AccountAuthenticatorsWebauthn()

### Community 118 - "Endpoint Hook: authentication-account #118"
Cohesion: 0.40
Nodes (5): getAllauthClientV1AuthEmailVerify(), getGetAllauthClientV1AuthEmailVerifyQueryKey(), getGetAllauthClientV1AuthEmailVerifyQueryOptions(), getGetAllauthClientV1AuthEmailVerifyUrl(), useGetAllauthClientV1AuthEmailVerify()

### Community 119 - "Endpoint Hook: authentication-providers #119"
Cohesion: 0.40
Nodes (5): getAllauthClientV1AuthProviderSignup(), getGetAllauthClientV1AuthProviderSignupQueryKey(), getGetAllauthClientV1AuthProviderSignupQueryOptions(), getGetAllauthClientV1AuthProviderSignupUrl(), useGetAllauthClientV1AuthProviderSignup()

### Community 120 - "Endpoint Hook: authentication-webauthn-login #120"
Cohesion: 0.40
Nodes (5): getAllauthClientV1AuthWebauthnAuthenticate(), getGetAllauthClientV1AuthWebauthnAuthenticateQueryKey(), getGetAllauthClientV1AuthWebauthnAuthenticateQueryOptions(), getGetAllauthClientV1AuthWebauthnAuthenticateUrl(), useGetAllauthClientV1AuthWebauthnAuthenticate()

### Community 121 - "Endpoint Hook: authentication-webauthn-login #121"
Cohesion: 0.40
Nodes (5): getAllauthClientV1AuthWebauthnLogin(), getGetAllauthClientV1AuthWebauthnLoginQueryKey(), getGetAllauthClientV1AuthWebauthnLoginQueryOptions(), getGetAllauthClientV1AuthWebauthnLoginUrl(), useGetAllauthClientV1AuthWebauthnLogin()

### Community 122 - "Endpoint Hook: authentication-webauthn-login #122"
Cohesion: 0.40
Nodes (5): getAllauthClientV1AuthWebauthnReauthenticate(), getGetAllauthClientV1AuthWebauthnReauthenticateQueryKey(), getGetAllauthClientV1AuthWebauthnReauthenticateQueryOptions(), getGetAllauthClientV1AuthWebauthnReauthenticateUrl(), useGetAllauthClientV1AuthWebauthnReauthenticate()

### Community 123 - "Endpoint Hook: authentication-webauthn-signup #123"
Cohesion: 0.40
Nodes (5): getAllauthClientV1AuthWebauthnSignup(), getGetAllauthClientV1AuthWebauthnSignupQueryKey(), getGetAllauthClientV1AuthWebauthnSignupQueryOptions(), getGetAllauthClientV1AuthWebauthnSignupUrl(), useGetAllauthClientV1AuthWebauthnSignup()

### Community 124 - "tsconfig (money)"
Cohesion: 0.40
Nodes (4): exclude, extends, include, @olivin/config/tsconfig/base.json

### Community 125 - "tsconfig (schemas)"
Cohesion: 0.40
Nodes (4): exclude, extends, include, @olivin/config/tsconfig/base.json

### Community 132 - "qrcode-terminal.d (types)"
Cohesion: 0.50
Nodes (3): qrcode-terminal/vendor/QRCode, qrcode-terminal/vendor/QRCode/QRErrorCorrectLevel, QRCodeInstance

### Community 133 - "Endpoint Hook: profiles #133"
Cohesion: 0.50
Nodes (4): customersProfileChangeRolePartialUpdate(), getCustomersProfileChangeRolePartialUpdateMutationOptions(), getCustomersProfileChangeRolePartialUpdateUrl(), useCustomersProfileChangeRolePartialUpdate()

### Community 134 - "Endpoint Hook: profiles #134"
Cohesion: 0.50
Nodes (4): customersProfileCreate(), getCustomersProfileCreateMutationOptions(), getCustomersProfileCreateUrl(), useCustomersProfileCreate()

### Community 135 - "Endpoint Hook: profiles #135"
Cohesion: 0.50
Nodes (4): customersProfileDestroy(), getCustomersProfileDestroyMutationOptions(), getCustomersProfileDestroyUrl(), useCustomersProfileDestroy()

### Community 136 - "Endpoint Hook: profiles #136"
Cohesion: 0.50
Nodes (4): customersProfilePartialUpdate(), getCustomersProfilePartialUpdateMutationOptions(), getCustomersProfilePartialUpdateUrl(), useCustomersProfilePartialUpdate()

### Community 137 - "Endpoint Hook: profiles #137"
Cohesion: 0.50
Nodes (4): customersProfileUpdate(), getCustomersProfileUpdateMutationOptions(), getCustomersProfileUpdateUrl(), useCustomersProfileUpdate()

### Community 139 - "Endpoint Hook: account-2fa #139"
Cohesion: 0.50
Nodes (4): deleteAllauthClientV1AccountAuthenticatorsTotp(), getDeleteAllauthClientV1AccountAuthenticatorsTotpMutationOptions(), getDeleteAllauthClientV1AccountAuthenticatorsTotpUrl(), useDeleteAllauthClientV1AccountAuthenticatorsTotp()

### Community 140 - "Endpoint Hook: account-2fa #140"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AccountAuthenticatorsRecoveryCodesMutationOptions(), getPostAllauthClientV1AccountAuthenticatorsRecoveryCodesUrl(), postAllauthClientV1AccountAuthenticatorsRecoveryCodes(), usePostAllauthClientV1AccountAuthenticatorsRecoveryCodes()

### Community 141 - "Endpoint Hook: account-2fa #141"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AccountAuthenticatorsTotpMutationOptions(), getPostAllauthClientV1AccountAuthenticatorsTotpUrl(), postAllauthClientV1AccountAuthenticatorsTotp(), usePostAllauthClientV1AccountAuthenticatorsTotp()

### Community 142 - "Endpoint Hook: account-email #142"
Cohesion: 0.50
Nodes (4): deleteAllauthClientV1AccountEmail(), getDeleteAllauthClientV1AccountEmailMutationOptions(), getDeleteAllauthClientV1AccountEmailUrl(), useDeleteAllauthClientV1AccountEmail()

### Community 143 - "Endpoint Hook: account-email #143"
Cohesion: 0.50
Nodes (4): getPatchAllauthClientV1AccountEmailMutationOptions(), getPatchAllauthClientV1AccountEmailUrl(), patchAllauthClientV1AccountEmail(), usePatchAllauthClientV1AccountEmail()

### Community 144 - "Endpoint Hook: account-email #144"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AccountEmailMutationOptions(), getPostAllauthClientV1AccountEmailUrl(), postAllauthClientV1AccountEmail(), usePostAllauthClientV1AccountEmail()

### Community 145 - "Endpoint Hook: account-email #145"
Cohesion: 0.50
Nodes (4): getPutAllauthClientV1AccountEmailMutationOptions(), getPutAllauthClientV1AccountEmailUrl(), putAllauthClientV1AccountEmail(), usePutAllauthClientV1AccountEmail()

### Community 146 - "Endpoint Hook: account-webauthn #146"
Cohesion: 0.50
Nodes (4): deleteAllauthClientV1AccountAuthenticatorsWebauthn(), getDeleteAllauthClientV1AccountAuthenticatorsWebauthnMutationOptions(), getDeleteAllauthClientV1AccountAuthenticatorsWebauthnUrl(), useDeleteAllauthClientV1AccountAuthenticatorsWebauthn()

### Community 147 - "Endpoint Hook: account-webauthn #147"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AccountAuthenticatorsWebauthnMutationOptions(), getPostAllauthClientV1AccountAuthenticatorsWebauthnUrl(), postAllauthClientV1AccountAuthenticatorsWebauthn(), usePostAllauthClientV1AccountAuthenticatorsWebauthn()

### Community 148 - "Endpoint Hook: account-webauthn #148"
Cohesion: 0.50
Nodes (4): getPutAllauthClientV1AccountAuthenticatorsWebauthnMutationOptions(), getPutAllauthClientV1AccountAuthenticatorsWebauthnUrl(), putAllauthClientV1AccountAuthenticatorsWebauthn(), usePutAllauthClientV1AccountAuthenticatorsWebauthn()

### Community 149 - "Endpoint Hook: authentication-account #149"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthEmailVerifyMutationOptions(), getPostAllauthClientV1AuthEmailVerifyUrl(), postAllauthClientV1AuthEmailVerify(), usePostAllauthClientV1AuthEmailVerify()

### Community 150 - "Endpoint Hook: authentication-account #150"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthEmailVerifyResendMutationOptions(), getPostAllauthClientV1AuthEmailVerifyResendUrl(), postAllauthClientV1AuthEmailVerifyResend(), usePostAllauthClientV1AuthEmailVerifyResend()

### Community 151 - "Endpoint Hook: authentication-account #151"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthLoginMutationOptions(), getPostAllauthClientV1AuthLoginUrl(), postAllauthClientV1AuthLogin(), usePostAllauthClientV1AuthLogin()

### Community 152 - "Endpoint Hook: authentication-account #152"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthPhoneVerifyMutationOptions(), getPostAllauthClientV1AuthPhoneVerifyUrl(), postAllauthClientV1AuthPhoneVerify(), usePostAllauthClientV1AuthPhoneVerify()

### Community 153 - "Endpoint Hook: authentication-account #153"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthPhoneVerifyResendMutationOptions(), getPostAllauthClientV1AuthPhoneVerifyResendUrl(), postAllauthClientV1AuthPhoneVerifyResend(), usePostAllauthClientV1AuthPhoneVerifyResend()

### Community 154 - "Endpoint Hook: authentication-account #154"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthReauthenticateMutationOptions(), getPostAllauthClientV1AuthReauthenticateUrl(), postAllauthClientV1AuthReauthenticate(), usePostAllauthClientV1AuthReauthenticate()

### Community 155 - "Endpoint Hook: authentication-account #155"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthSignupMutationOptions(), getPostAllauthClientV1AuthSignupUrl(), postAllauthClientV1AuthSignup(), usePostAllauthClientV1AuthSignup()

### Community 156 - "Endpoint Hook: authentication-login-by-code #156"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthCodeConfirmMutationOptions(), getPostAllauthClientV1AuthCodeConfirmUrl(), postAllauthClientV1AuthCodeConfirm(), usePostAllauthClientV1AuthCodeConfirm()

### Community 157 - "Endpoint Hook: authentication-login-by-code #157"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthCodeRequestMutationOptions(), getPostAllauthClientV1AuthCodeRequestUrl(), postAllauthClientV1AuthCodeRequest(), usePostAllauthClientV1AuthCodeRequest()

### Community 158 - "Endpoint Hook: authentication-login-by-code #158"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthCodeResendMutationOptions(), getPostAllauthClientV1AuthCodeResendUrl(), postAllauthClientV1AuthCodeResend(), usePostAllauthClientV1AuthCodeResend()

### Community 159 - "Endpoint Hook: authentication-providers #159"
Cohesion: 0.50
Nodes (4): getPostAllauthBrowserV1AuthProviderRedirectMutationOptions(), getPostAllauthBrowserV1AuthProviderRedirectUrl(), postAllauthBrowserV1AuthProviderRedirect(), usePostAllauthBrowserV1AuthProviderRedirect()

### Community 160 - "Endpoint Hook: authentication-providers #160"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthProviderSignupMutationOptions(), getPostAllauthClientV1AuthProviderSignupUrl(), postAllauthClientV1AuthProviderSignup(), usePostAllauthClientV1AuthProviderSignup()

### Community 161 - "Endpoint Hook: authentication-providers #161"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthProviderTokenMutationOptions(), getPostAllauthClientV1AuthProviderTokenUrl(), postAllauthClientV1AuthProviderToken(), usePostAllauthClientV1AuthProviderToken()

### Community 162 - "Endpoint Hook: authentication-webauthn-login #162"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthWebauthnAuthenticateMutationOptions(), getPostAllauthClientV1AuthWebauthnAuthenticateUrl(), postAllauthClientV1AuthWebauthnAuthenticate(), usePostAllauthClientV1AuthWebauthnAuthenticate()

### Community 163 - "Endpoint Hook: authentication-webauthn-login #163"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthWebauthnLoginMutationOptions(), getPostAllauthClientV1AuthWebauthnLoginUrl(), postAllauthClientV1AuthWebauthnLogin(), usePostAllauthClientV1AuthWebauthnLogin()

### Community 164 - "Endpoint Hook: authentication-webauthn-login #164"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthWebauthnReauthenticateMutationOptions(), getPostAllauthClientV1AuthWebauthnReauthenticateUrl(), postAllauthClientV1AuthWebauthnReauthenticate(), usePostAllauthClientV1AuthWebauthnReauthenticate()

### Community 165 - "Endpoint Hook: authentication-webauthn-signup #165"
Cohesion: 0.50
Nodes (4): getPostAllauthClientV1AuthWebauthnSignupMutationOptions(), getPostAllauthClientV1AuthWebauthnSignupUrl(), postAllauthClientV1AuthWebauthnSignup(), usePostAllauthClientV1AuthWebauthnSignup()

### Community 166 - "Endpoint Hook: authentication-webauthn-signup #166"
Cohesion: 0.50
Nodes (4): getPutAllauthClientV1AuthWebauthnSignupMutationOptions(), getPutAllauthClientV1AuthWebauthnSignupUrl(), putAllauthClientV1AuthWebauthnSignup(), usePutAllauthClientV1AuthWebauthnSignup()

### Community 173 - "index.d (tokens)"
Cohesion: 0.50
Nodes (3): Colors, ColorScale, FontSizeEntry

## Knowledge Gaps
- **1306 isolated node(s):** `{ loadEnv }`, `NativeIntent`, `{ defineConfig }`, `expoConfig`, `path` (+1301 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1434 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `react-native` connect `Mobile Auth Forms` to `Mobile Dependencies A`, `Platform & CSRF`, `Platform Component Factory`, `Mobile Auth Service`, `Auth Provider & Layout`, `Mobile Screen Layout`, `Account Settings Screen`, `TOTP QR Code (Web)`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `dependencies` connect `Mobile Dependencies B` to `Mobile Dependencies A`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `expo-router` connect `Mobile Auth Forms` to `authredirect (app)`, `Mobile Dependencies A`, `Auth Provider & Layout`, `Mobile Screen Layout`, `Account Settings Screen`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **What connects `{ loadEnv }`, `NativeIntent`, `{ defineConfig }` to the rest of the system?**
  _1306 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Auth Account API Client` be split into smaller, more focused modules?**
  _Cohesion score 0.024691358024691357 - nodes in this community are weakly interconnected._
- **Should `Addresses API Client` be split into smaller, more focused modules?**
  _Cohesion score 0.03184005923731951 - nodes in this community are weakly interconnected._
- **Should `Addresses Zod Schemas` be split into smaller, more focused modules?**
  _Cohesion score 0.03278688524590164 - nodes in this community are weakly interconnected._