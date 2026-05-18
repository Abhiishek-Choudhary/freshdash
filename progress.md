# FreshDash — Project Progress

> **Last updated:** 2026-05-17 (Dark mode, Hindi i18n, SearchBar polish)  
> **Purpose:** Handoff document for backend development. The mobile app is built and running on mock data; this file describes what exists, what the API must provide, and how to integrate.

---

## 1. Executive Summary

**FreshDash** is a hyperlocal grocery delivery mobile app (React Native + Expo + TypeScript), similar to Instamart/Blinkit. The frontend is **production-ready in structure** and uses **mock APIs** until the Node.js + Express backend is connected.

| Item | Status |
|------|--------|
| Mobile app scaffold | ✅ Complete |
| Stitch UI — Home, Store + Filter, Product Scanner | ✅ Complete |
| Tab bar back / forward navigation (customer) | ✅ Complete |
| Search screen UI + shared `SearchBar` component | ✅ Complete |
| Dark mode toggle (Profile → App Preferences) | ✅ Complete |
| English / Hindi language toggle + i18n | ✅ Complete |
| Mock product images (unique per product id) | ✅ Complete |
| Stitch UI — Store, Product, Cart (earlier batch) | ✅ Complete |
| Stitch UI — Profile, Order Tracking, Checkout (Customer) | ✅ Complete |
| Stitch UI — Vendor Dashboard, Inventory | ✅ Complete |
| Stitch UI — Delivery Dashboard, Order Detail (#FD-7721) | ✅ Complete |
| Auth flow (OTP + JWT + roles) | ✅ UI + mock service |
| User / Vendor / Delivery modules + role tab navigators | ✅ Complete |
| State management (Zustand + TanStack Query) | ✅ Complete |
| Socket.IO client (order tracking) | ✅ Wired, needs server |
| REST API integration | ⏳ **Backend required** |
| Push notifications | ❌ Not started |
| Payment gateway (Razorpay/Stripe/UPI) | ⏳ UI built, gateway TBD |

---

## 2. Environment & Run Instructions

### Requirements
- **Node.js:** `>=20` (tested on **v24.12.0**)
- **npm:** `>=10`
- **Expo Go** on device/emulator, or Android Studio / Xcode for native builds

### Commands
```bash
cd c:\Users\akc64\project-1
npm install
npx expo install --fix    # align Expo SDK peer deps
npm run typecheck
npx expo start
```

### Environment variables (`.env`)
```env
EXPO_PUBLIC_API_URL=http://localhost:3000/api
EXPO_PUBLIC_SOCKET_URL=http://localhost:3000
```

### Demo login (mock mode)
1. Enter any phone number → Continue  
2. OTP screen → enter **`123456`**  
3. Sign up with role **Customer**, **Vendor**, or **Delivery Partner** to route to the correct app shell  

### Disable mocks (when backend is ready)
Set `USE_MOCK = false` in:
- `src/services/authService.ts`
- `src/services/storeService.ts`
- `src/services/orderService.ts`

---

## 3. Tech Stack (Mobile)

| Layer | Technology | Version (approx.) |
|-------|------------|-------------------|
| Framework | Expo SDK | 53 |
| UI | React Native | 0.79 |
| Language | TypeScript | 5.8 |
| Navigation | React Navigation 7 | stack + bottom tabs |
| Client state | Zustand | 5 |
| Server state | TanStack Query | 5 |
| HTTP | Axios | 1.9 |
| Forms | React Hook Form + Zod | 7 / 3 |
| Realtime | socket.io-client | 4.8 |
| Persistence | AsyncStorage + Expo Secure Store | — |

---

## 4. Project Structure

```
src/
├── api/
│   ├── client.ts          # Axios instance + JWT interceptors
│   ├── endpoints.ts       # All REST path constants
│   ├── mockData.ts        # Mock stores, products, orders, etc.
│   ├── vendorMockData.ts  # Vendor dashboard, inventory, orders
│   └── deliveryMockData.ts # Delivery stats, active order, FD-7721
├── components/
│   ├── ui/                # Button, Input, Card, Badge, Loader, ...
│   ├── layout/            # AppHeader, BottomTabBar, RoleTabBar, VendorHeader
│   ├── product/           # ProductCard, CategoryPill
│   ├── cart/              # CartItemRow, FloatingCartBar
│   ├── order/             # OrderStepper (tracking timeline)
│   └── profile/           # ProfileMenuCard
├── constants/
│   ├── theme.ts           # Colors, spacing, typography (Stitch palette)
│   ├── enums.ts           # UserRole, OrderStatus, ...
│   └── routes.ts          # Route name constants
├── contexts/
│   ├── ThemeContext.tsx   # Light/dark mode
│   ├── ToastContext.tsx
│   ├── ModalContext.tsx
│   └── SocketContext.tsx  # Socket.IO subscriptions
├── features/auth/
│   └── schemas.ts         # Zod validation for login/signup/OTP
├── hooks/
│   ├── useStores.ts       # TanStack Query: stores, products, search
│   ├── useOrders.ts
│   └── useCart.ts
├── navigation/
│   ├── AppNavigator.tsx   # Role-based root navigator
│   ├── AuthNavigator.tsx
│   ├── UserNavigator.tsx + UserTabNavigator.tsx
│   ├── VendorNavigator.tsx
│   └── DeliveryNavigator.tsx
├── screens/
│   ├── auth/              # Login, Signup, OTP
│   ├── user/              # Home, Search, Cart, Checkout, ...
│   ├── vendor/            # Dashboard, Inventory, Orders, Analytics
│   └── delivery/          # Dashboard, Order Detail, Earnings, History, Profile
├── services/              # API service layer (mock/real switch)
├── store/                 # Zustand: auth, cart, theme
├── types/                 # TypeScript interfaces
└── utils/                 # format, storage, errorHandler
```

---

## 5. User Roles & Navigation

| Role | Enum value | App shell after login |
|------|------------|------------------------|
| Customer | `user` | Bottom tabs: Home, Search, Orders, Profile |
| Vendor | `vendor` | Bottom tabs: Dashboard, Orders, Inventory, Analytics |
| Delivery Partner | `delivery_partner` | Bottom tabs: Dashboard, Earnings, History, Profile |
| Admin | `admin` | Not implemented on mobile yet |

Role is chosen at **signup** and returned in `AuthResponse.user.role`.

---

## 6. Features Built (Mobile)

### 6.1 Authentication
| Screen | Route | Notes |
|--------|-------|-------|
| Login | `Login` | Phone → sends OTP |
| Signup | `Signup` | Name, email, phone, role picker |
| OTP | `OtpVerification` | 6-digit code; demo: `123456` |

**JWT:** Stored in Expo Secure Store (`accessToken`, `refreshToken`). Axios interceptor attaches `Authorization: Bearer <token>` and refreshes on 401 via `POST /auth/refresh`.

### 6.2 Customer (User)
| Screen | Description |
|--------|-------------|
| Home | **Stitch UI:** location header, search + barcode, promo banner, nearby shops, categories, daily essentials, compact cart bar |
| Search | Product search (`q` query param) |
| Store Products | Stitch grid: categories + **Filter** button, product cards, floating cart bar |
| Product Scanner | **Stitch UI:** camera overlay, scan frame, product detect card, Add to Cart |
| Product Detail | Hero image, nutrition, related products, add to cart |
| Cart | Address, items, coupon, order summary, checkout CTA |
| Checkout | **Stitch UI:** address card + map preview, delivery slot grid (Express), UPI/Cards/COD payment, INR order summary, FRESH50 coupon, sticky Place Order |
| Orders | Order history list |
| Order Tracking | **Stitch UI:** Order #FD-8291, ETA window, horizontal stepper (Ordered→Delivered), rider map visual, Marcus Chen partner card, expandable summary, support FAB |
| Addresses | List + add (UI only) |
| Notifications | List |
| Profile | **Stitch UI:** avatar + edit, Gold Member badge, My Orders / Addresses / Payment cards, settings group (Notifications badge), logout |

### 6.3 Vendor (Stitch UI)
| Screen | Component | Description |
|--------|-----------|-------------|
| Dashboard | `VendorDashboardScreen` | Revenue $2,482.50, active orders, recent orders (Accept/Reject, Ready for Pickup), inventory alerts, FAB |
| Inventory | `VendorInventoryScreen` | Search, filters, category pills, LOW STOCK / SOLD OUT badges, In Stock toggles, orange FAB |
| Orders | `VendorOrdersScreen` | Full order list tab |
| Analytics | `VendorAnalyticsScreen` | Revenue metrics tab |
| Product Form | `VendorProductFormScreen` | Add/edit product (stack modal) |

**Vendor bottom tabs:** Dashboard • Orders • Inventory • Analytics (green pill active state)

### 6.4 Delivery Partner (Stitch UI)
| Screen | Component | Description |
|--------|-----------|-------------|
| Dashboard | `DeliveryDashboardScreen` | Online toggle, earnings/deliveries/time stats, active delivery card, hotspots |
| Order Detail | `DeliveryOrderDetailScreen` | **#FD-7721** — map, pickup/delivery route, items, driver earnings, Confirm Pick Up |
| Earnings | `DeliveryEarningsScreen` | Today/week/month earnings |
| History | `DeliveryHistoryScreen` | Past deliveries list |
| Profile | `DeliveryProfileScreen` | Driver profile + logout |

**Delivery bottom tabs:** Dashboard • Earnings • History • Profile (green pill active state)

### 6.5 Cross-cutting
- Design system matching Stitch (green `#1B7A4E`, orange cart `#F97316`)
- Toast notifications, confirm modals
- Empty states, loading spinners
- Light/dark theme

---

## 7. REST API Contract (Backend Must Implement)

**Base URL:** `{EXPO_PUBLIC_API_URL}` → e.g. `http://localhost:3000/api`  
**Auth header:** `Authorization: Bearer <accessToken>`  
**Error shape (expected by mobile):**
```json
{
  "message": "Human readable error",
  "code": "OPTIONAL_ERROR_CODE"
}
```

### 7.1 Auth

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/auth/login` | `{ "phone": "+1234567890" }` | `{ "otpSent": true }` |
| POST | `/auth/signup` | `{ "name", "email", "phone", "role" }` | `{ "otpSent": true }` |
| POST | `/auth/verify-otp` | `{ "phone", "otp" }` | `AuthResponse` (see types below) |
| POST | `/auth/refresh` | `{ "refreshToken" }` | `{ "accessToken" }` |
| POST | `/auth/logout` | — | `204` or `{ "success": true }` |
| GET | `/auth/me` | — | `User` |

```typescript
// AuthResponse
{
  "user": {
    "id": "string",
    "name": "string",
    "email": "string",
    "phone": "string",
    "role": "user" | "vendor" | "delivery_partner" | "admin",
    "avatarUrl": "string?"
  },
  "tokens": {
    "accessToken": "string",
    "refreshToken": "string"
  }
}
```

### 7.2 Stores & Products

| Method | Path | Query | Response |
|--------|------|-------|----------|
| GET | `/stores/nearby` | `lat`, `lng` (recommended) | `Store[]` |
| GET | `/stores/:id` | — | `Store` |
| GET | `/stores/:id/products` | `category?` | `Product[]` |
| GET | `/products/:id` | — | `Product` |
| GET | `/products/search` | `q` | `Product[]` |
| GET | `/products/scan` | `barcode` or image upload | `Product` (for scanner) |
| GET | `/products/:id/related` | — | `Product[]` |

```typescript
// Store
{
  "id", "name", "imageUrl",
  "rating": number, "reviewCount": number,
  "deliveryTimeMin": number, "deliveryTimeMax": number,
  "deliveryFee": number, "distanceKm": number,
  "categories": string[], "isOpen": boolean
}

// Product
{
  "id", "storeId", "name", "description", "imageUrl",
  "price": number, "originalPrice"?: number,
  "unit": string, "category": string,
  "badge"?: "ORGANIC" | "SALE",
  "inStock": boolean, "stockCount": number,
  "tags"?: string[],
  "nutrition"?: { "calories", "fiber", "sugar", "vitaminC" },
  "pricePerKg"?: number
}
```

### 7.3 Cart (optional server sync)

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/cart` | — | `CartItem[]` |
| POST | `/cart/sync` | `{ items: CartItem[] }` | `CartItem[]` |

> **Note:** Cart is currently **client-only (Zustand)**. Backend can add sync later.

### 7.4 Orders

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/orders` | — | `Order[]` |
| GET | `/orders/:id` | — | `Order` |
| POST | `/orders` | See below | `Order` |
| GET | `/orders/:id/track` | — | `{ status, estimatedDelivery?, driverLocation? }` |

```typescript
// POST /orders body (suggested)
{
  "storeId": "string",
  "items": [{ "productId": "string", "quantity": number }],
  "addressId": "string",
  "deliverySlotId": "string",       // e.g. "express", "slot1"
  "couponCode"?: "string",           // e.g. "FRESH50"
  "paymentMethod": "upi" | "card" | "cod"
}

// Order
{
  "id", "storeId", "storeName",
  "items": CartItem[],
  "status": OrderStatus,
  "address": Address,
  "summary": {
    "subtotal", "deliveryFee", "taxes", "discount", "total"
  },
  "createdAt": "ISO8601",
  "estimatedDelivery"?: "string",
  "estimatedDeliveryWindow"?: "string",  // "12:45 PM – 1:00 PM"
  "displayId"?: "string",                // "FD-8291"
  "isOnTime"?: boolean,
  "deliveryPartner"?: DeliveryPartner
}

// DeliveryPartner
{
  "id": "string",
  "name": "string",
  "avatarUrl": "string",
  "rating": number,
  "title": "string"                      // "Your Delivery Hero"
}
```

**OrderStatus enum:**  
`pending` → `confirmed` → `preparing` → `ready_for_pickup` → `out_for_delivery` → `delivered` | `cancelled`

### 7.5 Checkout helpers (recommended)

| Method | Path | Response |
|--------|------|----------|
| GET | `/checkout/slots` | `DeliverySlot[]` |
| GET | `/checkout/preview` | `{ items, summary, address }` |
| POST | `/coupons/validate` | `{ valid, discount }` |

```typescript
// DeliverySlot
{ "id": "string", "label": "Today", "sublabel": "15 - 20 Mins", "isExpress"?: boolean }

// CheckoutSummary (INR or locale-aware)
{
  "itemTotal": number,
  "deliveryFee": number,
  "deliveryFeeStrikethrough"?: number,
  "taxes": number,
  "discount": number,
  "total": number,
  "couponCode"?: string
}
```

### 7.6 Addresses

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/addresses` | — | `Address[]` |
| POST | `/addresses` | `Address` (no id) | `Address` |
| PUT | `/addresses/:id` | Partial `Address` | `Address` |
| DELETE | `/addresses/:id` | — | `204` |

### 7.7 Notifications

| Method | Path | Response |
|--------|------|----------|
| GET | `/notifications` | `Notification[]` |
| PATCH | `/notifications/:id/read` | `Notification` |

### 7.8 Vendor APIs

| Method | Path | Notes |
|--------|------|-------|
| GET | `/vendor/dashboard` | `VendorStats` + `VendorRecentOrder[]` + inventory alerts |
| GET | `/vendor/products` | `VendorInventoryItem[]` |
| POST | `/vendor/products` | Create product |
| PUT | `/vendor/products/:id` | Update product (incl. `inStock`, `stockCount`) |
| DELETE | `/vendor/products/:id` | Delete product |
| GET | `/vendor/orders` | Orders for vendor's store |
| PATCH | `/vendor/orders/:id/accept` | Accept order |
| PATCH | `/vendor/orders/:id/reject` | Reject order |
| PATCH | `/vendor/orders/:id/ready` | Mark ready for pickup |
| GET | `/vendor/analytics` | Weekly revenue, AOV, fulfillment rate |

```typescript
// VendorStats
{ todayRevenue, revenueChange, activeOrders, inDelivery }

// VendorRecentOrder
{ id, itemCount, total, timeAgo, status: 'new'|'preparing'|'on_way', statusLabel }

// VendorInventoryItem
{ id, name, category, unit, price, imageUrl, stockCount, inStock, isLowStock, isSoldOut }
```

### 7.9 Delivery APIs

| Method | Path | Notes |
|--------|------|-------|
| GET | `/delivery/dashboard` | `DeliveryDashboardStats` + `DeliveryActiveOrder` + hotspots |
| GET | `/delivery/assignments` | `DeliveryAssignment[]` |
| GET | `/delivery/assignments/:id` | `DeliveryOrderDetail` (full order for #FD-7721 screen) |
| PATCH | `/delivery/partner/online` | Toggle online status |
| POST | `/delivery/assignments/:id/pickup` | Confirm pickup |
| POST | `/delivery/assignments/:id/deliver` | Confirm delivery |
| GET | `/delivery/earnings` | Today / week / month breakdown |
| GET | `/delivery/history` | Completed deliveries |

```typescript
// DeliveryDashboardStats
{ earningsToday, earningsChange, deliveriesCount, completionRate, timeOnline, shiftEndsIn }

// DeliveryActiveOrder
{ id, displayId, customerName, itemCount, etaMinutes, addressLine1, addressLine2, mapImageUrl }

// DeliveryOrderDetail
{
  id, displayId, estimatedMinutes, distanceMiles, mapImageUrl,
  pickup: { storeName, address, phone },
  delivery: { customerName, address, instructions },
  items: [{ id, name, unit, quantity, imageUrl }],
  subtotal, driverEarnings, pickupConfirmed, status
}
```

---

## 8. Socket.IO Events (Realtime)

**Server URL:** `EXPO_PUBLIC_SOCKET_URL` (no `/api` suffix)

### Client → Server
| Event | Payload |
|-------|---------|
| `subscribe:order` | `{ orderId: string }` |
| `unsubscribe:order` | `{ orderId: string }` |

### Server → Client
| Event | Payload |
|-------|---------|
| `order:{orderId}:update` | `{ orderId, status: OrderStatus, message?: string }` |

**Used on:** `OrderTrackingScreen` — updates timeline when status changes.

**Recommended additional events (not yet in mobile):**
- `notification:new` → push in-app toast
- `delivery:location` → driver GPS for map

---

## 9. Mobile State & Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Screens   │────▶│    Hooks     │────▶│    Services     │
└─────────────┘     └──────────────┘     └────────┬────────┘
       │                    │                       │
       │                    │                       ▼
       ▼                    ▼              ┌─────────────────┐
┌─────────────┐     ┌──────────────┐     │  Axios client   │
│ Zustand     │     │ TanStack     │     │  (or mock)      │
│ auth, cart  │     │ Query        │     └─────────────────┘
└─────────────┘     └──────────────┘
```

| Store | Persists | Contents |
|-------|----------|----------|
| `authStore` | Secure Store (tokens) | `user`, `isAuthenticated` |
| `cartStore` | Memory only | `items`, `couponCode`, totals |
| `themeStore` | AsyncStorage | `light` / `dark` / `system` |

---

## 10. Backend Recommendations

### Suggested stack
- **Runtime:** Node.js 20+  
- **Framework:** Express.js  
- **Database:** PostgreSQL + Prisma/TypeORM  
- **Cache:** Redis (sessions, OTP, cart optional)  
- **Auth:** JWT (access 15m, refresh 7d) + OTP via SMS (Twilio/MSG91)  
- **Realtime:** Socket.IO on same server or Redis adapter for scale  
- **Storage:** S3/Cloudinary for product images  
- **Payments:** Razorpay or Stripe (mobile has placeholder UI)

### Suggested DB entities
`User`, `Store`, `Product`, `Category`, `Cart`, `CartItem`, `Order`, `OrderItem`, `Address`, `Notification`, `DeliveryAssignment`, `Coupon`, `Payment`

### Priority order for backend sprints
1. **Auth** (login, signup, OTP, JWT, `/me`)  
2. **Stores + Products** (nearby, list, search, detail)  
3. **Orders** (create, list, status updates)  
4. **Addresses**  
5. **Vendor APIs** (products CRUD, vendor orders)  
6. **Delivery APIs** (assignments, pickup/deliver)  
7. **Socket.IO** order events  
8. **Notifications**  
9. **Payments** integration  

---

## 11. Stitch UI Screens Reference

All screens below are implemented. File paths point to the React Native screen component.

| # | Screen | Component | Key UI elements |
|---|--------|-----------|-----------------|
| 1 | Organic Market | `StoreProductsScreen` | Category pills, 2-col grid, floating cart bar |
| 2 | Product Detail | `ProductDetailScreen` | Hero image, nutrition grid, related products |
| 3 | Shopping Cart | `CartScreen` | Address card, coupon, order summary, checkout CTA |
| 4 | **Profile** | `ProfileScreen` | Gold Member badge, menu cards, settings group, logout |
| 5 | **Order Tracking** | `OrderTrackingScreen` | `#FD-8291`, stepper, rider map, delivery partner, support FAB |
| 6 | **Checkout** | `CheckoutScreen` | Address + map, slot grid, UPI/COD, INR summary, FRESH50 |
| 7 | **Vendor Dashboard** | `VendorDashboardScreen` | Revenue stats, recent orders, inventory alerts |
| 8 | **Vendor Inventory** | `VendorInventoryScreen` | Search, filters, stock toggles, Add Product FAB |
| 9 | **Delivery Dashboard** | `DeliveryDashboardScreen` | Online toggle, active delivery, hotspots |
| 10 | **Delivery Order Detail** | `DeliveryOrderDetailScreen` | Map, route, items, Confirm Pick Up (#FD-7721) |
| 11 | **Home** | `HomeScreen` | Promo banner, shop carousel, essentials grid, barcode → scanner |
| 12 | **Product Scanner** | `ProductScannerScreen` | Camera UI, scan animation, detected product card |

Design tokens: `src/constants/theme.ts`  
Primary green: `#1B7A4E` / `#006D33` | Cart/Support orange: `#F97316` | Background: `#F8F9FB`

### Demo navigation
| Role | How to access |
|------|----------------|
| Customer | Sign up as **Customer** → Home tab; barcode icon → Product Scanner |
| Vendor | Sign up as **Vendor** → Dashboard tab (default) |
| Delivery | Sign up as **Delivery Partner** → Dashboard → Order Details |

---

## 12. Customer UX — Navigation & Search (2026-05-17)

### Tab bar history (`←` / `→`)
- **Location:** Row above bottom tabs on the **customer** app (`CustomTabBar`).
- **Back:** Walks through visited screens (tabs + stack: product detail, cart, store, etc.). Falls back to React Navigation `goBack()` when history is empty.
- **Forward:** Restores screens after going back (browser-style).
- **Implementation:**
  - `src/store/navigationHistoryStore.ts` — Zustand history stack + index
  - `src/navigation/NavigationHistoryTracker.tsx` — records route changes on the user stack
  - `src/navigation/userNavigationHistory.ts` — capture / apply serialized routes
  - `src/navigation/UserNavigator.tsx` — mounts the tracker

### Search UI
- **Component:** `src/components/ui/SearchBar.tsx` — pill shape, green search icon, clear button, optional readonly mode (Home).
- **Search tab:** Trending chips, category shortcuts, empty-state illustration, result count header.
- **Home:** Tapping the search bar opens the Search tab; barcode button opens Product Scanner.

### Mock images
- `src/constants/mockImages.ts` — `mockImage(seed)` uses **picsum.photos** with one unique seed per product id (`e1`, `p1`, …).
- Hero banners still use verified Unsplash URLs where noted in `MOCK_UNSPLASH`.

### Dark mode & language (2026-05-17)
- **Profile → App Preferences:** Dark Mode switch + English / हिंदी segmented control.
- **Persistence:** `@freshdash/theme` (light/dark), `@freshdash/language` (`en` | `hi`).
- **i18n:** `src/i18n/translations.ts`, `LanguageProvider`, `useLanguage().t('key')` — Home, Search, Profile, tab labels.
- **Dark UI:** Refined `Colors.dark` (white primary text `#F9FAFB`, elevated surfaces `#1A2332`); `NavigationContainer` respects `isDark`; status bar flips light/dark.

### SearchBar (Google-style)
- No border; pill shape (`#F1F3F4` light / `#2D2D2D` dark).
- Soft shadow; green glow on focus.
- Web: `outlineStyle: 'none'` on `TextInput` to remove default black focus ring.
- Trending chips: borderless pills.
- Shared on Home (readonly) and Search tab.

### Store & category screens
- **Green Valley (s2):** Added snacks/beverages/vegetables mock products — store page no longer empty.
- **Category match:** `matchesCategory()` maps `Dairy` → `Dairy & Eggs`, etc.
- **Category browse:** Hero card, item count, 2-column grid with names/prices/add button.
- **Store products:** Store banner, category pills, empty/loading states, product count line.

---

## 13. Known Gaps / Future Work

| Item | Priority |
|------|----------|
| Connect all services to real API | P0 |
| Server-side cart sync | P2 |
| Push notifications (FCM) | P1 |
| Razorpay/Stripe checkout | P1 |
| Admin mobile panel | P3 |
| Skeleton loaders on all lists | P2 |
| Image upload for vendor products | P1 |
| Geolocation for nearby stores | P1 |
| Rate limiting / OTP throttling | P0 (backend) |

---

## 14. Files to Share with Backend Cursor Session

Give the backend agent these paths:
- `progress.md` (this file)
- `src/api/endpoints.ts`
- `src/types/index.ts`
- `src/constants/enums.ts`
- `src/services/*.ts`
- `src/api/mockData.ts` (example payloads)

**Suggested backend prompt:**
> Build a Node.js + Express + PostgreSQL API for FreshDash using the contracts in `progress.md` and `src/api/endpoints.ts`. Match request/response types in `src/types/index.ts`. Implement JWT auth with OTP, Socket.IO for order updates, and role-based routes for user/vendor/delivery.

---

## 15. Changelog

| Date | Change |
|------|--------|
| 2026-05-16 | Initial mobile app: Expo 52, all modules, mock data |
| 2026-05-16 | Upgraded to Expo SDK 53, Node 24, added `progress.md`, verified `tsc` + `expo start` |
| 2026-05-16 | Built Stitch Profile, Order Tracking (#FD-8291), Checkout (INR, slots, UPI) screens |
| 2026-05-16 | Built Vendor Dashboard + Inventory, Delivery Dashboard + Order #FD-7721; role tab navigators |
| 2026-05-16 | Rebuilt Home (promo, shops, essentials), Store Filter btn, Product Scanner screen |
| 2026-05-17 | Fixed web deps (`expo-asset`); unique mock images via picsum per product id |
| 2026-05-17 | Customer tab bar back/forward history; `SearchBar` + Search screen redesign |
| 2026-05-17 | Profile dark mode + EN/HI language; Google-style borderless SearchBar; dark theme polish |
| 2026-05-17 | Redesigned Your Orders: OrderCard, Active/Past/All tabs, thumbnails, track & reorder |
| 2026-05-17 | Fixed empty Green Valley store (s2 products); category fuzzy match; Store/Category UI polish |
