# KisanAI OS

KisanAI OS — AI-based agriculture assistant platform. A FastAPI + SQLite backend with a layered architecture (Controller → Service → Repository → Database) for farmers, crops, soil, disease, live weather and agricultural advisory.

## Tech Stack

- Python 3.11
- FastAPI
- Uvicorn
- Pydantic v2 / Pydantic Settings
- SQLAlchemy 2.0 (ORM)
- Alembic (database migrations)
- SQLite

## Folder Structure

```
KisanAI-OS/
├── main.py                        # Entry point (uvicorn)
├── requirements.txt
├── kisanai.db                     # SQLite database
├── .env                           # Local configuration (not committed)
├── mobile/                        # Flutter (Android) mobile app
│   └── README.md                  # Mobile run/test/build guide
├── alembic/                       # Database migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│       ├── 0001_baseline.py
│       └── 0002_relationships_and_users.py
└── config/
    ├── settings.py                # Pydantic settings (loads .env)
    ├── app_config.py              # Application configuration
    └── core/
        ├── database.py            # SQLAlchemy engine / session
        ├── logger.py              # Logger
        ├── utils.py               # Utility helpers
        ├── exceptions.py          # AppError / NotFound / Conflict
        ├── schemas/               # Pydantic request/response models
        ├── api/
        │   ├── main.py            # FastAPI application (main app)
        │   ├── auth.py            # JWT/bcrypt auth design stub (Phase 3)
        │   ├── routes.py          # Route constants
        │   ├── request.py         # Request wrapper
        │   └── response.py        # Response wrapper
        ├── controllers/           # Controllers
        ├── models/                # SQLAlchemy ORM models
        ├── repositories/          # Repositories
        └── services/              # Services
```

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Server starts at http://localhost:8000

Interactive API docs: http://localhost:8000/docs

Host/port and hot-reload are configurable via `HOST`, `PORT` and `RELOAD`
environment variables (see `.env.example`). For production startup, HTTPS,
PostgreSQL and persistent media requirements, see
**[DEPLOYMENT.md](DEPLOYMENT.md)**.

## Database Migrations

Schema changes are managed with Alembic. To migrate an existing
database (or a fresh one) to the latest schema:

```bash
alembic upgrade head
```

Current migration history:

- `0001_baseline` — baseline schema (farmers, crops, soils, weather, diseases)
- `0002_relationships_and_users` — foreign keys, unique constraints, weather PK, users table
- `0003_weather_location_index` — weather location index
- `0004_normalize_relationships_weather` — normalized weather relationships

## Error Responses

The API returns structured errors instead of silent HTTP 200s:

| Status | Meaning |
|---|---|
| 404 | Resource not found |
| 409 | Duplicate / conflict (e.g. unique constraint) |
| 422 | Request validation failed |
| 502 | Weather provider unavailable |
| 500 | Internal server error |

## Authentication (Phase 3)

JWT + bcrypt based authentication.

- Passwords are hashed with bcrypt and never stored or returned in plain text.
- Login returns a JWT access token (`HS256`), signed with `SECRET_KEY`.
- `SECRET_KEY`, `JWT_ALGORITHM` and `JWT_EXPIRE_MINUTES` are configured
  via `.env` / settings.
- An admin account is bootstrapped idempotently on startup from
  `ADMIN_USERNAME` / `ADMIN_PASSWORD`.
- Existing farmer/crop/disease/soil/advisory read and write endpoints are
  now protected: read/list endpoints require any authenticated user
  (`get_current_user`); all writes plus `/api/uploads` require the
  `admin` role. `/api/weather`, `/api/auth/register` and `/api/auth/token`
  remain public. Role-based protection is available via
  `require_role("admin" | "farmer" | "expert")`.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Home / welcome |
| GET | `/health` | Liveness/readiness probe (no secrets leaked; 503 if DB down) |
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/token` | OAuth2 form login → JWT token |
| GET | `/api/auth/me` | Current user (bearer token) |
| GET | `/api/weather` | Live weather (Open-Meteo) |
| POST | `/api/advisory` | Generate agricultural advisory |
| POST | `/api/farmers` | Create farmer |
| GET | `/api/farmers` | List farmers |
| GET | `/api/farmers/{farmer_id}` | Get farmer |
| PUT | `/api/farmers/{farmer_id}` | Update farmer |
| DELETE | `/api/farmers/{farmer_id}` | Delete farmer |
| POST | `/api/crops` | Create crop |
| GET | `/api/crops` | List crops |
| GET | `/api/crops/{crop_id}` | Get crop |
| PUT | `/api/crops/{crop_id}` | Update crop |
| DELETE | `/api/crops/{crop_id}` | Delete crop |
| POST | `/api/diseases` | Create disease |
| GET | `/api/diseases` | List diseases |
| GET | `/api/diseases/{disease_id}` | Get disease |
| PUT | `/api/diseases/{disease_id}` | Update disease |
| DELETE | `/api/diseases/{disease_id}` | Delete disease |
| POST | `/api/soils` | Create soil |
| GET | `/api/soils` | List soils |
| GET | `/api/soils/{soil_id}` | Get soil |
| PUT | `/api/soils/{soil_id}` | Update soil |
| DELETE | `/api/soils/{soil_id}` | Delete soil |

## Mobile App

The Android client lives in [`mobile/`](mobile/README.md) — a Hindi-first
Flutter app covering login/session handling, a dashboard, live weather,
farmer/crop/soil/disease foundations, photo-based disease diagnosis and the
AI recommendation engine.

```bash
cd mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000   # physical device
flutter test
flutter build apk --debug
```

The default `API_BASE_URL` is `http://10.0.2.2:8000` (Android emulator → host
machine). See `mobile/README.md` for full instructions.

## Advisory Request Example

```json
POST /api/advisory
{
    "crop_name": "Wheat",
    "soil_type": "Loamy",
    "ph": 6.8,
    "moisture": 45,
    "nitrogen": 50,
    "phosphorus": 25,
    "potassium": 30,
    "temperature": 30.3,
    "humidity": 81,
    "condition": "Overcast",
    "wind_speed": 6.0
}
```
