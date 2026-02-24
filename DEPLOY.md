# Deploying GeneWeb to Render.com (Free)

## What You Get (Free Tier)

- **Web Service**: App running 24/7 (spins down after 15 min inactivity, wakes on next request)
- **PostgreSQL Database**: 256 MB storage, free for 90 days

---

## One-Click Deploy with Blueprint

1. Go to [https://dashboard.render.com](https://dashboard.render.com) and sign up / log in.
2. Click **New → Blueprint** and connect the GitHub repository:
   `EpitechPGE45-2025/G-ING-900-PAR-9-1-legacy-1`
3. Render detects `render.yaml` and auto-configures:
   - A **free PostgreSQL** database (`geneweb-db`)
   - A **free web service** (`geneweb`) built from the `Dockerfile`, deploying from the `main` branch
4. Click **Apply** — Render builds and deploys everything.
5. Your app will be live at `https://geneweb-XXXX.onrender.com`.

---

## Manual Setup (Alternative)

### 1. Create a PostgreSQL Database

1. In the Render dashboard, click **New → PostgreSQL**.
2. Name: `geneweb-db`, Plan: **Free**, then click **Create Database**.
3. Copy the **Internal Database URL**.

### 2. Create a Web Service

1. Click **New → Web Service**.
2. Connect the repo `EpitechPGE45-2025/G-ING-900-PAR-9-1-legacy-1`, branch: `main`.
3. Configure:
   - **Name**: `geneweb`
   - **Runtime**: **Docker**
   - **Plan**: **Free**
4. Add environment variable:
   - Key: `DATABASE_URL`
   - Value: paste the Internal Database URL from step 1
5. Click **Create Web Service**.

---

## After Deployment

- Tables are **auto-created** on first startup via the `lifespan` handler.
- To run Alembic migrations manually, use the Render **Shell** tab:
  ```bash
  cd /app && PYTHONPATH=src alembic upgrade head
  ```

## Environment Variables

| Variable        | Description                  | Default              |
|-----------------|------------------------------|----------------------|
| `DATABASE_URL`  | PostgreSQL connection string | `sqlite:///./test.db`|

## Troubleshooting

- **Slow first load**: Free tier spins down after inactivity. First request may take ~30s.
- **Database expired**: Render free PostgreSQL lasts 90 days. Create a new one and update `DATABASE_URL`.

## Local Development

Without `DATABASE_URL` set, the app uses SQLite:

```bash
cd src
uvicorn geneweb.main:app --reload
```
