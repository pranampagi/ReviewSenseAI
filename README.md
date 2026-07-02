# ReviewSense AI

E-commerce review intelligence platform: ingest product reviews, run three ML pipelines in parallel (sentiment, fake detection, aspect scores), and visualize insights in a Vue dashboard.

---

## Architecture

```
Browser (Vue SPA — planned)
        │ REST + JWT
        ▼
FastAPI (backend/app)
  ├── /auth        → register, login, refresh, me
  ├── /products    → CRUD (owner-scoped)
  ├── /reviews     → ingest, list, bulk CSV
  └── /analyze     → sentiment trend, fake alerts, aspects, rerun
        │
        ├── SQL (SQLite dev / PostgreSQL prod)
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
- Node.js 20+
- Optional: [uv](https://github.com/astral-sh/uv) for faster installs

---

## Backend setup

```bash
cd backend

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r ml/requirements-ml.txt

cp .env.example .env
# Set SECRET_KEY and DATABASE_URL at minimum

alembic upgrade head

docker run -d --name reviewsense-mongo -p 27017:27017 mongo:7

uvicorn app.main:app --reload --port 8000
```

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)  
- Health: [http://localhost:8000/health](http://localhost:8000/health)

---

## ML model setup (run once per machine)

Artifacts are gitignored under `backend/ml/models/`. Train locally:

```bash
cd backend

# Fake review detector (XGBoost)
python -m ml.train_fake_detector --generate-synthetic
# or: python -m ml.train_fake_detector --data path/to/labelled.csv

# Aspect sentiment (PyTorch biLSTM)
python -m ml.aspect.train --generate-synthetic --epochs 10
# or: python -m ml.aspect.train --data path/to/aspect_labels.csv --epochs 10

# DistilBERT downloads automatically on first API startup (~250MB)
```

Expected artifacts:


| File                             | Model                  |
| -------------------------------- | ---------------------- |
| `ml/models/xgb_model.pkl`        | Fake detector          |
| `ml/models/tfidf_vectorizer.pkl` | Feature pipeline       |
| `ml/models/aspect_model.pt`      | Aspect biLSTM weights  |
| `ml/models/aspect_vocab.json`    | Aspect tokenizer vocab |


---

## API reference (implemented)

### Auth — `/auth`


| Method | Path        | Description                     |
| ------ | ----------- | ------------------------------- |
| POST   | `/register` | Create account → JWT pair       |
| POST   | `/login`    | Login → JWT pair                |
| POST   | `/refresh`  | Bearer refresh token → new pair |
| GET    | `/me`       | Current user profile            |


### Products — `/products` (Bearer required)


| Method | Path    | Description                                   |
| ------ | ------- | --------------------------------------------- |
| GET    | `/`     | List own products (`page`, `limit`, `search`) |
| POST   | `/`     | Create product                                |
| GET    | `/{id}` | Product detail                                |
| PUT    | `/{id}` | Partial update                                |
| DELETE | `/{id}` | Delete → 204                                  |


### Reviews — `/reviews` (Bearer required)


| Method | Path                  | Description                                          |
| ------ | --------------------- | ---------------------------------------------------- |
| POST   | `/`                   | Submit single review → triggers ML pipeline          |
| POST   | `/bulk-upload`        | CSV upload (`product_id` + file)                     |
| GET    | `/`                   | List with filters (`product_id`, `sentiment`, dates) |
| GET    | `/{id}`               | Review + `analysis_result` when complete             |
| GET    | `/bulk-jobs/{job_id}` | CSV job status (MongoDB)                             |


### Analysis — `/analyze` (Bearer required)


| Method | Path                           | Description                              |
| ------ | ------------------------------ | ---------------------------------------- |
| GET    | `/sentiment-trend?product_id=` | Daily sentiment aggregates               |
| GET    | `/fake-alerts`                 | Paginated fake review alerts             |
| POST   | `/aspects`                     | Score arbitrary text (`{"text": "..."}`) |
| GET    | `/aspect-summary/{product_id}` | Avg aspect scores for a product          |
| POST   | `/rerun/{review_id}`           | Re-queue ML pipeline → 202               |


### System


| Method | Path      | Description        |
| ------ | --------- | ------------------ |
| GET    | `/health` | API + Mongo status |


---

## Environment variables


| Variable          | Required | Default / notes                        |
| ----------------- | -------- | -------------------------------------- |
| `SECRET_KEY`      | Yes      | JWT signing                            |
| `DATABASE_URL`    | Yes      | `sqlite+aiosqlite:///./reviewsense.db` |
| `MONGODB_URL`     | No       | `mongodb://localhost:27017`            |
| `MONGODB_DB_NAME` | No       | `reviewsense`                          |
| `HF_MODEL_ID`     | No       | DistilBERT SST-2 model id              |
| `ALLOWED_ORIGINS` | No       | CORS origins (comma-separated)         |


See [backend/.env.example](backend/.env.example).

---

## Repository layout

```
ReviewSenseAI/
├── README.md
├── backend/
│   ├── app/           # FastAPI app, routers, services, models
│   ├── ml/            # ML pipelines and training scripts
│   │   ├── pipeline.py, sentiment.py, fake_detector.py
│   │   ├── aspect/    # dataset, model, train, infer
│   │   ├── data/      # sample CSVs for local training
│   │   └── models/    # saved artifacts (gitignored)
│   ├── alembic/
│   └── requirements.txt
└── frontend/          # Vue app
```

---

## Troubleshooting

### Motor / PyMongo import error

```bash
pip install -r requirements.txt --force-reinstall
```

`pymongo>=4.6,<4.10` is pinned for Motor 3.7.x compatibility.

### Reviews stuck in `pending` or `failed`

- Ensure fake-detector pickles exist (`ml.train_fake_detector`)
- Ensure aspect model exists (`ml.aspect.train`)
- First startup downloads DistilBERT (needs network)
- Check uvicorn logs for ML errors

