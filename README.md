# ReviewSense AI

E-commerce review intelligence platform: ingest product reviews, run ML analysis (sentiment, fake detection, aspect scores), and visualize insights in a Vue dashboard.

Full build specification and remaining commits: see [ReviewSenseAI.md](ReviewSenseAI.md).

---

## Prerequisites

- **Python 3.11+** (3.13 may work; if Motor fails to import, use 3.11 or pin `pymongo` as in `requirements.txt`)
- **MongoDB 7** (local or Docker) for Commit #4 health check `mongo: connected`
- Optional: **uv** or **pip** + virtualenv

---

## Backend setup

```bash
cd backend

# 1. Virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
# or: uv pip install -r requirements.txt

# 3. Environment
cp .env.example .env
# Edit .env — required: SECRET_KEY, DATABASE_URL (see .env.example)

# 4. SQL migrations (Commit #3)
alembic revision --autogenerate -m "initial_schema"   # first time only
alembic upgrade head

# 5. MongoDB (Commit #4)
docker run -d --name reviewsense-mongo -p 27017:27017 mongo:7
# Ensure MONGODB_URL and MONGODB_DB_NAME in .env match your instance

# 6. Run API
uvicorn app.main:app --reload --port 8000
# or: uv run uvicorn app.main:app --reload
```

- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)  
- Health: [http://localhost:8000/health](http://localhost:8000/health)

### Expected health response

```json
{
  "status": "ok",
  "env": "development",
  "mongo": "connected"
}
```

If MongoDB is not running, the API still starts; `"mongo"` will be `"error"`.

---

## Environment variables


| Variable          | Required | Description                                   |
| ----------------- | -------- | --------------------------------------------- |
| `SECRET_KEY`      | Yes      | JWT signing key (min ~32 chars in production) |
| `DATABASE_URL`    | Yes      | e.g. `sqlite+aiosqlite:///./reviewsense.db`   |
| `MONGODB_URL`     | No       | Default `mongodb://localhost:27017`           |
| `MONGODB_DB_NAME` | No       | Default `reviewsense`                         |
| `ALLOWED_ORIGINS` | No       | Comma-separated CORS origins                  |
| `APP_ENV`         | No       | `development`                                 |


See [backend/.env.example](backend/.env.example) for the full list including future ML settings.

---

## Database models (SQL)


| Table              | Purpose                                                     |
| ------------------ | ----------------------------------------------------------- |
| `users`            | Accounts (email, hashed password)                           |
| `products`         | Catalog items owned by a user                               |
| `reviews`          | Review text, rating 1–5, status (`pending` → `complete`)    |
| `analysis_results` | ML output per review (sentiment, fake score, aspect floats) |


On startup, `main.py` runs `Base.metadata.create_all` for local SQLite convenience. Use **Alembic** for versioned schema changes.

---

## MongoDB collections


| Collection    | Purpose                                                      |
| ------------- | ------------------------------------------------------------ |
| `raw_reviews` | Full review text + metadata (char/word counts, CSV row info) |
| `ingest_logs` | Bulk upload job status (accepted/errors counts)              |


Helpers: `insert_raw_review()`, `insert_ingest_log()` in `app/mongo_collections.py`.

---

## Troubleshooting

### `ImportError: cannot import name '_QUERY_OPTIONS' from 'pymongo.cursor'`

Motor and PyMongo versions are incompatible. Reinstall with pinned deps:

```bash
pip install -r requirements.txt --force-reinstall
```

`requirements.txt` includes `pymongo>=4.6,<4.10` for Motor 3.7.x.

### Alembic / async SQLite

Migrations use async SQLAlchemy via `alembic/env.py`. Run commands from the `backend/` directory so `app` imports resolve.

### `reviewsense.db` not in git

SQLite files are listed in `.gitignore`; each developer generates their own local DB.

---

## Development workflow

1. Implement one commit block from `ReviewSenseAI.md`.
2. Run manual tests (health, migrations, Mongo as applicable).
3. Commit with the exact message from the spec.

---

## License / portfolio

Portfolio project demonstrating FastAPI, dual-database design, and ML-serving patterns. See `ReviewSenseAI.md` for the complete roadmap.