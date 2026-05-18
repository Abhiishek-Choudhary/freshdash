# FreshDash Backend — Progress & API Integration Guide

> **Audience:** Frontend / React Native team  
> **Last updated:** 2026-05-18  
> **Stack:** Django 5 + DRF + SQLite/PostgreSQL + Socket.IO (uvicorn ASGI)  
> **Product contract:** `progress.md` (feature spec from mobile repo)

Use **this file** for backend status **and** full REST/Socket integration details. Match TypeScript types in `project-1/src/types/index.ts` and paths in `src/api/endpoints.ts`.

---

## Quick start (frontend)

### Base URLs

| Env var (Expo) | Example | Notes |
|----------------|---------|--------|
| `EXPO_PUBLIC_API_URL` | `http://192.168.1.10:8000/api` | **Must include** `/api` suffix |
| `EXPO_PUBLIC_SOCKET_URL` | `http://192.168.1.10:8000` | **No** `/api` suffix |

Local default in mobile `client.ts` is port **3000** — change to **8000** (or run uvicorn on 3000).

### Headers (authenticated routes)

```http
Content-Type: application/json
Authorization: Bearer <accessToken>
```

### JSON casing

All request/response bodies use **camelCase** (`accessToken`, `storeId`, `deliveryFee`, …).

### IDs

Resource IDs are **UUID strings** unless noted (e.g. delivery slot `id` is `"express"`).

### Error shape

```json
{
  "message": "Human readable error",
  "code": "OPTIONAL_ERROR_CODE"
}
```

Common codes: `not_found`, `forbidden`, `invalid_otp`, `validation_error`, `rate_limited` (429).

### Auth flow

1. `POST /api/auth/login` `{ "phone": "+919876543210" }` → `{ "otpSent": true }`
2. `POST /api/auth/verify-otp` `{ "phone", "otp" }` → `AuthResponse` (dev OTP: **`123456`**)
3. Store `tokens.accessToken` / `tokens.refreshToken` (Secure Store)
4. On **401**, `POST /api/auth/refresh` `{ "refreshToken" }` → `{ "accessToken" }`
5. `GET /api/auth/me` for profile bootstrap

**Signup:** `POST /api/auth/signup` `{ name, email, phone, role }` → `{ otpSent: true }` → same verify step.

**Roles** (`role` on user): `user` | `vendor` | `delivery_partner` | `admin`

### Disable mocks (mobile)

Set `USE_MOCK = false` in:

- `src/services/authService.ts`
- `src/services/storeService.ts`
- `src/services/orderService.ts`

Add vendor/delivery service calls for screens still on `vendorMockData` / `deliveryMockData`.

### Demo seed (`python manage.py seed_data`)

| Role | Phone | Password | OTP |
|------|-------|----------|-----|
| Customer | +919876543210 | password123 | 123456 |
| Vendor | +919876543211 | password123 | 123456 |
| Delivery | +919876543212 | password123 | 123456 |

Coupon: **`FRESH50`** (₹50 off, min order ₹200).  
Sample barcodes on products: `890e1`, `890p1`, etc.

### Health check

`GET /api/health` → `{ "status": "ok", "service": "freshdash-api" }` (no auth)

### Interactive docs

- Swagger: `http://localhost:8000/api/docs/`
- OpenAPI: `http://localhost:8000/api/schema/`

---

## Sprint status (backend)

| Sprint | Scope | Status |
|--------|--------|--------|
| S1 | §7 REST polish (track, checkout fields, stores list, vendor earnings, scan POST) | ✅ |
| S2 | Socket `notification:new`, `delivery:location`, location API | ✅ |
| S3 | Payments, SMS OTP hooks, FCM stub, rate limit | ✅ |
| S4 | Admin API, CDN, Redis Socket, signed webhooks | ⏳ |
| S5 | Mobile wire vendor/delivery off mocks | ⏳ Frontend |

---

## REST API reference

Legend: **Auth** = Bearer required unless marked Public.

---

### Auth — prefix `/api/auth/`

| Method | Path | Auth | Request body | Response |
|--------|------|------|--------------|----------|
| POST | `login` | Public | `{ phone }` | `{ otpSent: true }` |
| POST | `signup` | Public | `{ name, email, phone, role }` | `{ otpSent: true }` |
| POST | `verify-otp` | Public | `{ phone, otp }` | `AuthResponse` |
| POST | `refresh` | Public | `{ refreshToken }` | `{ accessToken }` |
| POST | `logout` | Bearer | `{ refreshToken }` optional | `204` empty |
| GET | `me` | Bearer | — | `User` |
| POST | `login/password` | Public | `{ phone, password }` | `AuthResponse` (bonus) |
| POST | `password/reset/request` | Public | `{ phone }` | `{ otpSent: true }` |
| POST | `password/reset/confirm` | Public | `{ phone, otp, newPassword }` | `{ success: true }` |

**AuthResponse**

```ts
{
  user: {
    id: string;
    name: string;
    email: string;
    phone: string;
    role: 'user' | 'vendor' | 'delivery_partner' | 'admin';
    avatarUrl?: string;
  };
  tokens: {
    accessToken: string;
    refreshToken: string;
  };
}
```

**Mobile mapping:** `API_ENDPOINTS.auth.*` → paths above (no `/api` prefix in constants; base URL includes it).

---

### Stores — prefix `/api/`

| Method | Path | Auth | Query | Response |
|--------|------|------|-------|----------|
| GET | `stores` | Public | `lat?`, `lng?` (sort by distance if both set) | `Store[]` |
| GET | `stores/nearby` | Public | `lat?`, `lng?` (defaults Delhi) | `Store[]` |
| GET | `stores/:storeId` | Public | — | `Store` |
| PATCH | `vendor/store/open` | Vendor | `{ isOpen: boolean }` | `Store` |

**Store**

```ts
{
  id: string;
  name: string;
  imageUrl: string;
  rating: number;
  reviewCount: number;
  deliveryTimeMin: number;
  deliveryTimeMax: number;
  deliveryFee: number;
  distanceKm: number;
  categories: string[];
  isOpen: boolean;
}
```

**Mobile mapping:** `stores.nearby`, `stores.detail(id)` — also use `GET /stores` for full list (`endpoints.ts` has `list: '/stores'`).

---

### Products — prefix `/api/`

| Method | Path | Auth | Query / body | Response |
|--------|------|------|--------------|----------|
| GET | `stores/:storeId/products` | Public | `category?` | `Product[]` |
| GET | `products/:productId` | Public | — | `Product` |
| GET | `products/search` | Public | `q?`, `category?` | `Product[]` |
| GET | `products/scan` | Public | `barcode` (required) | `Product` |
| POST | `products/scan` | Public | multipart: `image?`, `barcode?` | `Product` |
| GET | `products/:productId/related` | Public | — | `Product[]` |

**Product**

```ts
{
  id: string;
  storeId: string;
  name: string;
  brand?: string;
  description: string;
  imageUrl: string;
  price: number;
  originalPrice?: number;
  unit: string;
  category: string;
  badge?: 'ORGANIC' | 'SALE';
  inStock: boolean;
  stockCount: number;
  tags?: string[];
  nutrition?: { calories: string; fiber: string; sugar: string; vitaminC: string };
  pricePerKg?: number;
}
```

**Scan POST:** Send `multipart/form-data` with field `image` and/or `barcode`. If only image, server tries barcode decode (needs `pyzbar` on server; otherwise send `barcode` from client scanner).

---

### Cart — prefix `/api/` (optional server sync)

| Method | Path | Auth | Body | Response |
|--------|------|------|------|----------|
| GET | `cart` | Bearer | — | `CartItem[]` |
| POST | `cart/sync` | Bearer | `{ items: CartItem[] }` | `CartItem[]` |

**CartItem**

```ts
{
  productId: string;
  product: Product;
  quantity: number;
}
```

Cart can stay client-only (Zustand); these endpoints sync when needed.

---

### Orders & checkout — prefix `/api/`

| Method | Path | Auth | Body / query | Response |
|--------|------|------|--------------|----------|
| GET | `orders` | Customer | — | `Order[]` |
| POST | `orders` | Customer | see below | `Order` |
| GET | `orders/:orderId` | Bearer | — | `Order` |
| GET | `orders/:orderId/track` | Customer | — | track payload |
| GET | `checkout/slots` | Bearer | — | `DeliverySlot[]` |
| GET | `checkout/preview` | Bearer | `couponCode?` | preview payload |
| POST | `coupons/validate` | Bearer | `{ couponCode, subtotal }` | `{ valid, discount }` |

**POST /orders body**

```ts
{
  storeId: string;
  items: { productId: string; quantity: number }[];
  addressId: string;
  deliverySlotId: string;   // e.g. "express"
  couponCode?: string;      // e.g. "FRESH50"
  paymentMethod: 'upi' | 'card' | 'cod';
}
```

**Order**

```ts
{
  id: string;
  displayId?: string;              // e.g. "FD-8291"
  storeId: string;
  storeName: string;
  items: CartItem[];
  status: OrderStatus;
  address: Address;
  summary: {
    subtotal: number;
    deliveryFee: number;
    taxes: number;
    discount: number;
    total: number;
  };
  createdAt: string;               // ISO8601
  estimatedDelivery?: string;
  estimatedDeliveryWindow?: string;
  isOnTime?: boolean;
  deliveryPartner?: {
    id: string;
    name: string;
    avatarUrl: string;
    rating: number;
    title: string;                 // "Your Delivery Hero"
  };
}
```

**OrderStatus:** `pending` → `confirmed` → `preparing` → `ready_for_pickup` → `out_for_delivery` → `delivered` | `cancelled`

**GET /orders/:id/track**

```ts
{
  status: OrderStatus;
  estimatedDelivery?: string;      // ISO8601
  driverLocation?: {
    lat: number;
    lng: number;
    updatedAt?: string;
  };
}
```

**DeliverySlot**

```ts
{ id: string; label: string; sublabel?: string; isExpress?: boolean }
```

**GET /checkout/preview**

```ts
{
  items: CartItem[];
  summary: {
    itemTotal: number;
    deliveryFee: number;
    deliveryFeeStrikethrough?: number;
    taxes: number;
    discount: number;
    total: number;
    couponCode?: string;
  };
  address: Address | null;
}
```

---

### Addresses — prefix `/api/`

| Method | Path | Auth | Body | Response |
|--------|------|------|------|----------|
| GET | `addresses` | Bearer | — | `Address[]` |
| POST | `addresses` | Bearer | `Address` without `id` | `Address` |
| PUT | `addresses/:addressId` | Bearer | partial `Address` | `Address` |
| DELETE | `addresses/:addressId` | Bearer | — | `204` |

**Address**

```ts
{
  id: string;
  label: string;
  line1: string;
  line2: string;
  city: string;
  state: string;
  zipCode: string;
  isDefault: boolean;
}
```

---

### Notifications — prefix `/api/`

| Method | Path | Auth | Response |
|--------|------|------|----------|
| GET | `notifications` | Bearer | `Notification[]` |
| PATCH | `notifications/:notificationId/read` | Bearer | `Notification` |

**Notification**

```ts
{
  id: string;
  type: 'order' | 'delivery' | 'promo' | 'system';
  title: string;
  body: string;
  read: boolean;
  createdAt: string;
  data?: Record<string, string>;
}
```

---

### Vendor — prefix `/api/vendor/` (role: `vendor` or store staff)

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `dashboard` | — | dashboard payload |
| GET | `products` | — | `VendorInventoryItem[]` |
| POST | `products` | product fields; multipart `image?` | `VendorInventoryItem` / product |
| PUT | `products/:productId` | partial fields; `image?` | product |
| DELETE | `products/:productId` | — | `204` |
| GET | `orders` | — | `Order[]` |
| PATCH | `orders/:orderId/accept` | — | `Order` |
| PATCH | `orders/:orderId/prepare` | — | `Order` (extra) |
| PATCH | `orders/:orderId/reject` | — | `Order` |
| PATCH | `orders/:orderId/ready` | — | `Order` |
| GET | `analytics` | — | analytics payload |
| GET | `earnings` | — | `{ today, week, month }` |

**GET /vendor/dashboard**

```ts
{
  todayRevenue: number;
  revenueChange: number;
  activeOrders: number;
  inDelivery: number;
  recentOrders: {
    id: string;           // display id e.g. FD-1234
    itemCount: number;
    total: number;
    timeAgo: string;
    status: 'new' | 'preparing' | 'on_way';
    statusLabel: string;
  }[];
  inventoryAlerts: {
    id: string;
    name: string;
    stockLeft: number;
    imageUrl: string;
  }[];
}
```

**VendorInventoryItem**

```ts
{
  id: string;
  name: string;
  category: string;
  unit: string;
  price: number;
  imageUrl: string;
  stockCount: number;
  lowStockThreshold: number;
  inStock: boolean;
  isLowStock: boolean;
  isSoldOut: boolean;
}
```

**GET /vendor/analytics**

```ts
{
  weeklyRevenue: number;
  averageOrderValue: number;
  fulfillmentRate: number;
  orderCount: number;
}
```

**GET /vendor/earnings**

```ts
{ today: number; week: number; month: number }
```

**Mobile:** add `vendor.earnings` → `GET /vendor/earnings` in `endpoints.ts` if not present.

---

### Delivery partner — prefix `/api/delivery/` (role: `delivery_partner`)

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `dashboard` | — | dashboard payload |
| PATCH | `partner/online` | `{ isOnline: boolean }` | `{ isOnline: boolean }` |
| GET | `assignments` | — | `DeliveryAssignment[]` |
| GET | `assignments/:assignmentId` | — | `DeliveryOrderDetail` |
| PATCH | `assignments/:assignmentId/location` | `{ lat, lng }` | `{ orderId, lat, lng }` |
| POST | `assignments/:assignmentId/pickup` | — | `Order` |
| POST | `assignments/:assignmentId/deliver` | — | `Order` |
| GET | `earnings` | — | `{ today, week, month }` |
| GET | `history` | — | history items |

**GET /delivery/dashboard**

```ts
{
  earningsToday: number;
  earningsChange: number;
  deliveriesCount: number;
  completionRate: number;
  timeOnline: string;
  shiftEndsIn: string;
  activeOrder: DeliveryActiveOrder | null;
  hotspots: { id: string; name: string; surgeBonus: number }[];
}
```

**DeliveryAssignment** (list)

```ts
{
  id: string;
  orderId: string;
  storeName: string;
  customerAddress: string;
  status: OrderStatus;
  pickupConfirmed: boolean;
  deliveryConfirmed: boolean;
  earnings: number;
}
```

**DeliveryOrderDetail** (assignment detail — #FD-7721 screen)

```ts
{
  id: string;
  displayId: string;
  estimatedMinutes: string;
  distanceMiles: number;
  mapImageUrl: string;
  pickup: { storeName: string; address: string; phone: string };
  delivery: { customerName: string; address: string; instructions: string };
  items: { id: string; name: string; unit: string; quantity: number; imageUrl: string }[];
  subtotal: number;
  driverEarnings: number;
  pickupConfirmed: boolean;
  status: OrderStatus;
}
```

**Delivery partner app:** call `PATCH .../location` on a timer while on active delivery so customer map gets `delivery:location` events.

---

### Payments — prefix `/api/payments/`

| Method | Path | Auth | Body | Response |
|--------|------|------|------|----------|
| POST | `create` | Bearer | `{ orderId, provider? }` | payment intent |
| POST | `confirm` | Bearer | `{ paymentId }` | dev/mock confirm |
| POST | `webhook/:provider` | Public | provider payload | `{ received: true }` |

**POST /payments/create** (UPI/card — not COD)

```ts
// paymentRequired: false for COD
{
  paymentRequired: boolean;
  paymentId?: string;
  provider?: string;
  amount?: number;
  currency?: string;
  clientSecret?: string;    // Stripe client secret or Razorpay order id or mock_*
  orderId: string;
  paymentMethod?: string;
  status?: string;
}
```

**Flow:** Place order → `POST /payments/create` → open Razorpay/Stripe with `clientSecret` → on success call `POST /payments/confirm` in dev or rely on webhook in prod.

---

## Socket.IO integration

**URL:** `EXPO_PUBLIC_SOCKET_URL` (same host as API, no `/api`).

Use `socket.io-client` v4.

### Client → server

| Event | Payload |
|-------|---------|
| `subscribe:order` | `{ orderId: string }` |
| `unsubscribe:order` | `{ orderId: string }` |
| `subscribe:notifications` | `{ userId: string }` |
| `unsubscribe:notifications` | `{ userId: string }` |

### Server → client

| Event | Payload | When |
|-------|---------|------|
| `order:{orderId}:update` | `{ orderId, status, message? }` | Order status changes |
| `notification:new` | `Notification` object | New in-app notification |
| `delivery:location` | `{ orderId, lat, lng }` | Driver updates GPS |

**Order tracking screen:** subscribe to `subscribe:order` + listen for `order:{orderId}:update` and `delivery:location`.

**Notifications:** after login, `subscribe:notifications` with `user.id` + listen for `notification:new`.

---

## Mobile `endpoints.ts` → backend map

| Constant | Backend path |
|----------|----------------|
| `auth.login` | `POST /api/auth/login` |
| `auth.signup` | `POST /api/auth/signup` |
| `auth.verifyOtp` | `POST /api/auth/verify-otp` |
| `auth.refresh` | `POST /api/auth/refresh` |
| `auth.logout` | `POST /api/auth/logout` |
| `auth.me` | `GET /api/auth/me` |
| `stores.list` | `GET /api/stores` |
| `stores.nearby` | `GET /api/stores/nearby` |
| `stores.detail(id)` | `GET /api/stores/:id` |
| `stores.products(id)` | `GET /api/stores/:id/products` |
| `products.detail(id)` | `GET /api/products/:id` |
| `products.search` | `GET /api/products/search` |
| `products.related(id)` | `GET /api/products/:id/related` |
| — | `GET/POST /api/products/scan` |
| `cart.get` | `GET /api/cart` |
| `cart.sync` | `POST /api/cart/sync` |
| `orders.*` | `/api/orders...` |
| `addresses.*` | `/api/addresses...` |
| `notifications.*` | `/api/notifications...` |
| `vendor.dashboard` | `GET /api/vendor/dashboard` |
| `vendor.products` | `GET/POST /api/vendor/products` |
| `vendor.product(id)` | `PUT/DELETE /api/vendor/products/:id` |
| `vendor.orders` | `GET /api/vendor/orders` |
| `vendor.earnings` | `GET /api/vendor/earnings` |
| `delivery.dashboard` | `GET /api/delivery/dashboard` |
| `delivery.assignments` | `GET /api/delivery/assignments` |
| — | `GET /api/delivery/assignments/:id` |
| — | `PATCH /api/delivery/assignments/:id/location` |
| `delivery.confirmPickup(id)` | `POST /api/delivery/assignments/:id/pickup` |
| `delivery.confirmDelivery(id)` | `POST /api/delivery/assignments/:id/deliver` |
| — | `GET /api/delivery/earnings` |
| — | `GET /api/delivery/history` |
| — | `POST /api/payments/create` |
| — | `POST /api/payments/confirm` |

---

## Run backend locally

```powershell
cd Grocery-Delivery-Backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
py -3 manage.py migrate
py -3 manage.py seed_data
py -3 -m uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload
```

**Tests:** `py -3 -m pytest -q` (9 tests)

---

## Remaining backlog (not for v1 integration)

| Item | Notes |
|------|--------|
| Admin REST API | No mobile admin yet |
| S3/Cloudinary URLs | Local/media URLs in dev |
| Socket Redis adapter | Single server OK for dev |
| Signed payment webhooks | Use `confirm` in dev |
| `User.fcm_token` + register device | FCM optional via env |
| Vendor/delivery screens on mocks | Frontend wiring |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-18 | Full frontend API integration guide added to this file |
| 2026-05-18 | Sprints 1–3: REST gaps, sockets, payments, SMS/FCM/rate limit |
| 2026-05-18 | Signup OTP fix, `/api/health` |
