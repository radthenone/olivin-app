project-root/
├── app/ # Expo Router
│ ├── \_layout.tsx # Root z providers + Zustand hydration
│ ├── index.tsx # Initial redirect logic
│ │
│ ├── (auth)/ # Publiczne - logowanie/rejestracja
│ │ ├── \_layout.tsx # Stack layout bez protection
│ │ ├── login.tsx
│ │ ├── register.tsx
│ │ ├── forgot-password.tsx
│ │ ├── google-callback.tsx
│ │ └── mfa-verify.tsx
│ │
│ ├── (shop)/ # Główna aplikacja sklepu
│ │ ├── \_layout.tsx # Protected layout z redirect
│ │ ├── \_layout.web.tsx # Desktop layout (header/sidebar/footer)
│ │ ├── \_layout.native.tsx # Mobile layout
│ │ │
│ │ ├── (tabs)/ # Dolny tab bar na mobile
│ │ │ ├── \_layout.tsx
│ │ │ ├── index.tsx # Home/Featured products
│ │ │ ├── categories.tsx # Lista kategorii
│ │ │ ├── cart.tsx # Koszyk
│ │ │ └── profile.tsx # Profil użytkownika
│ │ │
│ │ ├── category/
│ │ │ └── [categoryId]/
│ │ │ ├── index.tsx # Lista podkategorii
│ │ │ └── [subcategoryId]/
│ │ │ ├── index.tsx # Lista produktów
│ │ │ └── [productId].tsx # Szczegóły produktu
│ │ │
│ │ ├── checkout/
│ │ │ ├── index.tsx # Przegląd koszyka
│ │ │ ├── shipping.tsx # Adres dostawy
│ │ │ ├── payment.tsx # Płatność
│ │ │ └── confirmation.tsx # Potwierdzenie
│ │ │
│ │ ├── orders/
│ │ │ ├── index.tsx # Historia zamówień
│ │ │ └── [orderId].tsx # Szczegóły zamówienia
│ │ │
│ │ └── search.tsx # Wyszukiwarka produktów
│ │
│ └── +not-found.tsx # 404 page
│
├── src/
│ ├── api/ # API Layer
│ │ ├── client.ts # Axios config + interceptors
│ │ ├── endpoints.ts # API URLs constants
│ │ └── services/
│ │ ├── auth.ts # Login, register, MFA, Google OAuth
│ │ ├── categories.ts # CRUD categories
│ │ ├── products.ts # Products, filters, search
│ │ ├── cart.ts # Cart operations
│ │ ├── orders.ts # Create order, history
│ │ └── payments.ts # Payment processing (Stripe/etc)
│ │
│ ├── components/ # UI Components
│ │ ├── ui/ # Reusable UI (buttons, inputs)
│ │ │ ├── Button.tsx
│ │ │ ├── Input.tsx
│ │ │ ├── Card.tsx
│ │ │ ├── Badge.tsx
│ │ │ └── Modal.tsx
│ │ │
│ │ ├── layout/
│ │ │ ├── Header.tsx
│ │ │ ├── Header.web.tsx
│ │ │ ├── Header.native.tsx
│ │ │ ├── Sidebar.tsx
│ │ │ ├── Footer.tsx
│ │ │ └── CategoryMenu.tsx
│ │ │
│ │ ├── product/
│ │ │ ├── ProductCard.tsx
│ │ │ ├── ProductList.tsx
│ │ │ ├── ProductFilter.tsx
│ │ │ ├── ProductDetails.tsx
│ │ │ └── ProductImage.tsx
│ │ │
│ │ ├── cart/
│ │ │ ├── CartItem.tsx
│ │ │ ├── CartSummary.tsx
│ │ │ └── CartIcon.tsx
│ │ │
│ │ └── order/
│ │ ├── OrderCard.tsx
│ │ ├── OrderStatus.tsx
│ │ └── OrderTimeline.tsx
│ │
│ ├── stores/ # Zustand stores
│ │ ├── authStore.ts # Auth state + actions
│ │ ├── cartStore.ts # Cart state + actions
│ │ ├── productsStore.ts # Products cache + filters
│ │ ├── categoriesStore.ts # Categories tree
│ │ └── ordersStore.ts # Orders history
│ │
│ ├── hooks/ # Custom hooks
│ │ ├── useAuth.ts # Wrapper dla authStore
│ │ ├── useCart.ts # Wrapper dla cartStore
│ │ ├── useBreakpoint.ts # Responsive breakpoints
│ │ ├── useSecureStorage.ts # expo-secure-store wrapper
│ │ └── useDebounce.ts # Debounce dla search
│ │
│ ├── types/ # TypeScript types
│ │ ├── auth.types.ts
│ │ ├── product.types.ts
│ │ ├── category.types.ts
│ │ ├── cart.types.ts
│ │ ├── order.types.ts
│ │ ├── payment.types.ts
│ │ └── index.ts
│ │
│ ├── lib/ # Utilities
│ │ ├── storage.ts # SecureStore dla tokenów
│ │ ├── formatters.ts # Format ceny, daty
│ │ ├── validators.ts # Zod schemas
│ │ └── constants.ts # App constants
│ │
│ └── styles/
│ └── tailwind.css # NativeWind global styles
│
├── backend/ # Django Backend
│ ├── manage.py
│ ├── config/
│ │ ├── settings/
│ │ │ ├── base.py
│ │ │ ├── development.py
│ │ │ └── production.py
│ │ ├── urls.py
│ │ └── wsgi.py
│ │
│ ├── apps/
│ │ ├── authentication/ # Custom auth (bez dj-rest-auth)
│ │ │ ├── models.py # Custom User model
│ │ │ ├── serializers.py # JWT serializers
│ │ │ ├── views.py # Login, register, MFA endpoints
│ │ │ ├── urls.py
│ │ │ └── utils.py # JWT helpers, Google OAuth
│ │ │
│ │ ├── categories/
│ │ │ ├── models.py # Category, Subcategory
│ │ │ ├── serializers.py
│ │ │ ├── views.py
│ │ │ └── urls.py
│ │ │
│ │ ├── products/
│ │ │ ├── models.py # Product, ProductImage, Review
│ │ │ ├── serializers.py
│ │ │ ├── views.py # CRUD, filters, search
│ │ │ └── urls.py
│ │ │
│ │ ├── cart/
│ │ │ ├── models.py # Cart, CartItem
│ │ │ ├── serializers.py
│ │ │ ├── views.py
│ │ │ └── urls.py
│ │ │
│ │ ├── orders/
│ │ │ ├── models.py # Order, OrderItem, OrderStatus
│ │ │ ├── serializers.py
│ │ │ ├── views.py
│ │ │ └── urls.py
│ │ │
│ │ └── payments/
│ │ ├── models.py # Payment, PaymentMethod
│ │ ├── serializers.py
│ │ ├── views.py # Stripe/PayPal integration
│ │ ├── urls.py
│ │ └── webhooks.py # Payment webhooks
│ │
│ └── requirements.txt
│
├── tailwind.config.js # Tailwind config
├── metro.config.js # Metro bundler config
├── babel.config.js # Babel with NativeWind preset
├── tsconfig.json
├── .env # Environment variables
└── package.json
