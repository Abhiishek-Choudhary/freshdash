# FreshDash Backend (Django REST Framework)

API backend for the FreshDash hyperlocal grocery delivery mobile app.

## Quick start

```bash
cd freshdash-backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_data
python manage.py runserver 0.0.0.0:8000
```

### Realtime (Socket.IO)

```bash
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload
```

## Mobile integration

In `project-1/.env`:

```env
EXPO_PUBLIC_API_URL=http://<YOUR_LAN_IP>:8000/api
EXPO_PUBLIC_SOCKET_URL=http://<YOUR_LAN_IP>:8000
```

Set `USE_MOCK = false` in:

- `src/services/authService.ts`
- `src/services/storeService.ts`
- `src/services/orderService.ts`

## Demo accounts (after `seed_data`)

| Role | Phone | Password | OTP (dev) |
|------|-------|----------|-----------|
| Customer | +919876543210 | password123 | 123456 |
| Vendor | +919876543211 | password123 | 123456 |
| Delivery | +919876543212 | password123 | 123456 |

## API docs

- Swagger: http://localhost:8000/api/docs/
- OpenAPI schema: http://localhost:8000/api/schema/

## PostgreSQL (optional)

```bash
docker compose up -d
# Set DATABASE_URL=postgres://freshdash:freshdash@localhost:5432/freshdash in .env
python manage.py migrate
```

Without `DATABASE_URL`, SQLite (`db.sqlite3`) is used automatically.

## Tests

```bash
pytest
```
