# TripWise — Smart Travel Planner

TripWise is a full-stack trip planner for collecting trip details, building a
day-by-day starting itinerary, estimating a budget, and tracking real expenses.
The code is organized into small React and Flask modules so the main flows are
straightforward to follow and extend.

## Features

- Account registration and login using Werkzeug password hashes and JWT access tokens.
- Private trip creation, viewing, editing, duplication, and deletion.
- Deterministic place ranking and itinerary generation, with interest, popularity,
  distance, cost, and time factors.
- Budget categories, spending totals, remaining budget, and Recharts visualization.
- Expense creation, editing, and deletion.
- OpenStreetMap/Leaflet markers for itinerary places.
- Sample hotel suggestions, a selectable stay, and PDF trip-plan download.
- Responsive landing page, trip dashboard, itinerary, map, budget, and profile.
- Explicit unavailable weather state if no weather provider is integrated.

## Technology and architecture

- Frontend: React, Vite, React Router, Axios, Recharts, Leaflet/React-Leaflet.
- Backend: Flask app factory, Flask-SQLAlchemy, Flask-CORS, Flask-JWT-Extended.
- Data: SQLite locally; SQLAlchemy accepts PostgreSQL connection URLs.
- `frontend/src/pages` contains route-level screens; `services/api.js` centralizes
  authenticated requests. Flask routes are in `backend/app/routes`, SQLAlchemy
  models in `backend/app/models`, and planning calculations in
  `backend/app/services`.

## Project structure

```text
TripWise/
├── frontend/src/
│   ├── components/   # Reusable auth form and map
│   ├── context/      # Persistent account session
│   ├── layouts/      # Authenticated workspace shell
│   ├── pages/        # Landing, account, trip and dashboard screens
│   ├── routes/       # Protected route
│   └── services/    # Axios API client
└── backend/
    ├── app/models/   # User, trip, place, itinerary, expense, budget and hotel
    ├── app/routes/   # Authentication, trip and public place endpoints
    ├── app/services/ # Budget, recommendation, itinerary, distance and sample data
    └── tests/        # Isolated Flask/SQLite API integration tests
```

## Development setup

Use two terminals from the `TripWise` folder:

```powershell
# Terminal 1: Flask API
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
Copy-Item .env.example .env
py run.py
```

```powershell
# Terminal 2: React application
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

The frontend is available at `http://localhost:5173`. Vite proxies `/api` to
`http://127.0.0.1:5000`, so the API base URL defaults to `/api`.

To run the backend tests:

```powershell
cd backend
py -m unittest discover -s tests -v
```

To create the production frontend bundle:

```powershell
cd frontend
npm run build
```

## Environment variables

Configure `backend/.env` from `backend/.env.example`:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Flask session/signing secret. Set a private random value outside local development. |
| `JWT_SECRET_KEY` | Signs access tokens. Use a separate private random value. |
| `DATABASE_URL` | SQLAlchemy URL. Defaults to a local SQLite database. |
| `FRONTEND_URL` | Allowed browser origin for Flask CORS. |
| `FLASK_DEBUG` | Defaults to `false`; enable only for local development. |

When either secret is omitted, a random process-local value is generated. Set
both explicitly for a deployment so tokens survive process restarts and all
workers use the same keys. Never commit `.env` files.

Set `VITE_API_BASE_URL` in `frontend/.env` only when the frontend should use an
API origin other than the Vite `/api` proxy.

For PostgreSQL, install the declared driver and set `DATABASE_URL`, for example:

```text
postgresql://tripwise_user:your_password@localhost:5432/tripwise
```

The startup schema upgrader adds new columns to existing tables without
dropping the original SQLite tables/data. For managed production deployments,
use reviewed database backups and a formal migration process when changing
schemas.

## API overview

Account routes:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me` (Bearer token)

Place routes:

- `GET /api/places`
- `GET /api/places/search?q=...&destination=...`

Trip routes below require `Authorization: Bearer <access_token>`:

- `GET|POST /api/trips`
- `GET|PUT|DELETE /api/trips/<id>`
- `POST /api/trips/<id>/duplicate`
- `POST /api/trips/<id>/generate`
- `POST /api/trips/<id>/reoptimize`
- `GET /api/trips/<id>/itinerary`
- `GET /api/trips/<id>/recommendations`
- `GET /api/trips/<id>/budget`; `POST /api/trips/<id>/budget/calculate`
- `GET|POST /api/trips/<id>/expenses`
- `PUT|DELETE /api/trips/<id>/expenses/<expense_id>`
- `GET /api/trips/<id>/hotels`; `POST|DELETE /api/trips/<id>/hotels[/<hotel_id>]`
- `GET /api/trips/<id>/weather`
- `GET /api/trips/<id>/export.pdf`
- `GET /api/health`

## Planning calculations

Place relevance uses a readable weighted score: interest match (40%),
popularity (20%), distance efficiency (15%), budget compatibility (15%), and
time compatibility (10%). The itinerary ranks places by that score, avoids
repeats, schedules visits within a 09:00–18:00 window, adds breaks and estimated
travel time, and respects a daily activity allowance. Haversine distance is
straight-line distance, not a road route. Budget category estimates are
preliminary allocations; expenses entered by the traveler drive actual spend
and remaining-budget values.

## Known limitations and next steps

- Place and hotel records are clearly marked sample data for Jaipur and Paris;
  generation reports when a destination has no sample catalog.
- Sample costs are estimates in the catalog's local currency. No currency
  conversion or hotel booking is performed.
- OpenStreetMap displays place pins, not turn-by-turn routes. Travel duration is
  an estimate based on straight-line distance and typical transport speeds.
- Weather reports unavailable until a real provider and server-side API
  integration are configured; no forecast is fabricated.
- Add a reviewed Alembic migration workflow before evolving a deployed
  PostgreSQL schema, and add provider integrations only with explicit source,
  error and freshness handling.
