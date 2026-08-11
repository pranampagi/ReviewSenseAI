# ReviewSense AI

E-commerce review intelligence platform: ingest product reviews, run three ML pipelines in parallel (sentiment, fake detection, aspect scores), and visualize insights in a Vue dashboard.

---

## Architecture

```
Browser (Vue 3 SPA — JavaScript)
        │ REST + JWT
        ▼
FastAPI (backend/app)
  ├── /auth        → register, login, refresh, me
  ├── /products    → CRUD (owner-scoped)
  ├── /reviews     → ingest, list, bulk CSV
  └── /analyze     → sentiment trend, fake alerts, aspects, rerun
        │
        ├── SQL (SQLite dev / PostgreSQL prod via asyncpg)
        │     users, products, reviews, analysis_results
        └── MongoDB
              raw_reviews, ingest_logs
        │
        ▼
ML layer (backend/ml)
  ├── sentiment.py      → HuggingFace DistilBERT
  ├── fake_detector.py  → XGBoost + TF-IDF
  └── aspect/           → PyTorch biLSTM (price, quality, shipping, service)
```

**Review flow:** `POST /reviews` → SQL + Mongo → background `run_full_pipeline()` → sentiment → fake → aspects → `analysis_results` row → `status: complete`.

---

## Prerequisites

- Python 3.11+ (3.13 works with pinned `pymongo` in `requirements.txt`)
- MongoDB 7 (local or Docker)
- Node.js 22+ (see `frontend/package.json` engines)
- Optional: [uv](https://github.com/astral-sh/uv), Docker Compose

---

## Quick start (local)

### Backend

```bash
cd backend

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r ml/requirements-ml.txt

cp .env.example .env
# Set SECRET_KEY and DATABASE_URL at minimum

alembic upgrade head

# Mongo only (if not using docker-compose):
docker run -d --name reviewsense-mongo -p 27017:27017 mongo:7

uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Frontend

```bash
cd frontend

npm install

cp .env.example .env.local
# VITE_API_URL=http://localhost:8000

npm run dev
```

Open http://localhost:5173 — register, then use Products and Analytics.

**Stack:** Vue 3, Vite, Pinia, Vue Router, Bootstrap 5, ApexCharts, Axios — **JavaScript only** (no TypeScript).

Use the **Dark / Light** toggle in the navbar to switch themes (preference is saved in `localStorage`).

---

## Docker Compose (Postgres + Mongo + API)

From the repo root:

```bash
# Train ML models first (artifacts are mounted into the API container)
cd backend
python -m ml.train_fake_detector --generate-synthetic
python -m ml.aspect.train --generate-synthetic --epochs 10
cd ..

docker compose up --build
```

Services:

| Service | Port | Notes |
|---------|------|--------|
| `postgres` | 5432 | `reviewsense` / `reviewsense` / db `reviewsense` |
| `mongo` | 27017 | Bulk-upload job logs + raw reviews |
| `api` | 8000 | Runs `alembic upgrade head` then uvicorn |

Point the API at Postgres with:

```env
DATABASE_URL=postgresql+asyncpg://reviewsense:reviewsense@localhost:5432/reviewsense
```

Alembic migrations are **async** (`alembic/env.py` uses `async_engine_from_config`) and work for both SQLite and PostgreSQL.

---

## ML model setup (run once per machine)

Artifacts are gitignored under `backend/ml/models/`. Train locally:

```bash
cd backend

python -m ml.train_fake_detector --generate-synthetic
python -m ml.aspect.train --generate-synthetic --epochs 10
# DistilBERT downloads automatically on first API startup (~250MB)
```

| File | Model |
|------|--------|
| `ml/models/xgb_model.pkl` | Fake detector |
| `ml/models/tfidf_vectorizer.pkl` | Feature pipeline |
| `ml/models/aspect_model.pt` | Aspect biLSTM weights |
| `ml/models/aspect_vocab.json` | Aspect tokenizer vocab |

---

## Backend tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest tests/ -v
```

With **uv**:

```bash
cd backend
uv run --with pytest --with pytest-asyncio --with httpx pytest tests/ -v
```

| File | Coverage |
|------|----------|
| `tests/test_auth.py` | Register, login, refresh, `/me`, health |
| `tests/test_reviews.py` | Product CRUD, review ingest, list, detail with analysis |
| `tests/test_ml.py` | Text preprocessing, feature pipeline, optional model inference |
| `tests/conftest.py` | In-memory SQLite, mocked MongoDB / background ML |

Tests use an isolated in-memory database — no MongoDB or DistilBERT download required for the API suite. ML model inference tests run when trained artifacts exist under `backend/ml/models/`.

---

## Continuous integration

GitHub Actions workflow: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

Runs on push to `main`/`master` and on pull requests:

| Job | Steps |
|-----|--------|
| Backend | install deps → `ruff check` → `pytest` |
| Frontend | `npm ci` → Vitest (`--passWithNoTests`) → `npm run build` |

---

## Frontend features

| Route | Description |
|-------|-------------|
| `/login`, `/register` | JWT authentication with route guards |
| `/dashboard` | Protected home |
| `/products` | Product card grid, search, pagination, add modal |
| `/products/:id` | Product detail — reviews + analytics tabs |
| `/analytics` | Sentiment trend chart + fake review alerts panel |

**Product detail — Reviews tab**
- **Add review** modal (`ReviewForm.vue`) — author, 1–5 stars, body (min 20 chars)
- **Bulk CSV upload** (`BulkUpload.vue`) — drag-drop, 10MB limit, progress bar, polls job status
- Review cards show global sentiment, fake, and pending badges when analysis runs
- Click a review card to open **ReviewDetailModal** — full ML breakdown, polls while pending, supports re-run

**Product detail — Analytics tab**
- **Aspect radar chart** (`AspectRadar.vue`) — average price / quality / shipping / service scores from `GET /analyze/aspect-summary/{product_id}`

**Analytics page**
- **Sentiment trend** (`SentimentChart.vue`) — product + date filters → `GET /analyze/sentiment-trend`
- **Fake review alerts** (`FakeAlertPanel.vue`) — paginated table with probability bars → `GET /analyze/fake-alerts`; **View full review** opens `ReviewDetailModal.vue`

**UI polish**
- Collapsible mobile navbar
- Dark / light theme toggle (`stores/theme.js`) with chart theming
- Shared ML badge styles in `custom.css`
- Review detail modal with live polling and re-run analysis

### Key components

| Component | Purpose |
|-----------|---------|
| `ReviewForm.vue` | Single review submission modal |
| `BulkUpload.vue` | CSV bulk ingest with job polling |
| `SentimentChart.vue` | Daily sentiment line + bar chart |
| `AspectRadar.vue` | Four-axis aspect sentiment radar |
| `FakeAlertPanel.vue` | Paginated fake-review alert table |
| `ReviewDetailModal.vue` | Full review + ML breakdown; polls pending analysis; re-run button |

---

## API reference

### Auth — `/auth`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/register` | Create account → JWT pair |
| POST | `/login` | Login → JWT pair |
| POST | `/refresh` | Bearer refresh token → new pair |
| GET | `/me` | Current user profile |

### Products — `/products` (Bearer required)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List own products (`page`, `limit`, `search`) |
| POST | `/` | Create product |
| GET | `/{id}` | Product detail |
| PUT | `/{id}` | Partial update |
| DELETE | `/{id}` | Delete → 204 |

### Reviews — `/reviews` (Bearer required)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Submit single review → triggers ML pipeline |
| POST | `/bulk-upload` | CSV upload (`product_id` + file) |
| GET | `/` | List with filters (`product_id`, `sentiment`, dates) |
| GET | `/{id}` | Review + `analysis_result` when complete |
| GET | `/bulk-jobs/{job_id}` | CSV job status (MongoDB) |

### Analysis — `/analyze` (Bearer required)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/sentiment-trend?product_id=` | Daily sentiment aggregates |
| GET | `/fake-alerts` | Paginated fake review alerts |
| POST | `/aspects` | Score arbitrary text |
| GET | `/aspect-summary/{product_id}` | Avg aspect scores for a product |
| POST | `/rerun/{review_id}` | Re-queue ML pipeline → 202 |

### System

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | API + Mongo status |

---

## Environment variables

| Variable | Required | Default / notes |
|----------|----------|-----------------|
| `SECRET_KEY` | Yes | JWT signing |
| `DATABASE_URL` | Yes | `sqlite+aiosqlite:///./reviewsense.db` or `postgresql+asyncpg://…` |
| `MONGODB_URL` | No | `mongodb://localhost:27017` |
| `MONGODB_DB_NAME` | No | `reviewsense` |
| `HF_MODEL_ID` | No | DistilBERT SST-2 model id |
| `ALLOWED_ORIGINS` | No | CORS origins (comma-separated) |
| `VITE_API_URL` | Frontend | `http://localhost:8000` |

See [backend/.env.example](backend/.env.example) and [frontend/.env.example](frontend/.env.example).

---

## Repository layout

```
ReviewSenseAI/
├── README.md
├── docker-compose.yml
├── .github/workflows/ci.yml
├── backend/
│   ├── Dockerfile
│   ├── app/              # FastAPI routers, services, models
│   ├── ml/               # ML pipelines + training scripts
│   ├── tests/            # pytest — auth, reviews, ML
│   ├── alembic/          # async migrations (SQLite + PostgreSQL)
│   ├── pytest.ini
│   ├── requirements.txt
│   └── requirements-dev.txt
└── frontend/             # Vue 3 SPA (JavaScript)
    ├── vercel.json       # SPA rewrites for Vercel
    ├── src/
    │   ├── api/axios.js
    │   ├── stores/       # auth.js, products.js, theme.js
    │   ├── assets/custom.css
    │   ├── views/        # Login, Products, ProductDetail, Analytics, …
    │   └── components/   # ReviewForm, BulkUpload, SentimentChart,
    │                       # AspectRadar, FakeAlertPanel, ReviewDetailModal
    └── vite.config.js
```

---

## Troubleshooting

### Motor / PyMongo import error

```bash
pip install -r requirements.txt --force-reinstall
```

`pymongo>=4.6,<4.10` is pinned for Motor 3.7.x compatibility.

### Reviews stuck in `pending` or `failed`

- Train fake-detector and aspect models (see ML setup above)
- First API startup downloads DistilBERT (needs network)
- Check uvicorn logs for ML errors

### Frontend cannot reach API

- Confirm backend is on port 8000
- Set `VITE_API_URL` in `frontend/.env.local`
- Ensure `ALLOWED_ORIGINS` includes `http://localhost:5173`

### Docker API image is large / slow to start

- Torch + Transformers are heavy; first DistilBERT download happens at container start
- Mount trained `backend/ml/models` (already configured in `docker-compose.yml`)

---

Portfolio project: FastAPI · SQLAlchemy · MongoDB · Scikit-learn · XGBoost · HuggingFace · PyTorch · Vue 3 · Bootstrap · ApexCharts · Docker · Vercel · GitHub Actions.
