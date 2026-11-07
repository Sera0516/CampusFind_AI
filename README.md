# CampusFind AI

A campus lost-and-found starter project with FastAPI, PostgreSQL, SQLAlchemy and an Angular UI.

## Important status
This ZIP provides a runnable CRUD/authentication foundation and a starter Angular UI. The semantic embedding search, pgvector persistence, image upload pipeline and RAG/LLM explanation layer are **not implemented yet**. They are planned extension points, not finished features. Do not expose this development setup publicly without adding authorization, validation, rate limiting, HTTPS and production secrets.

## 1. Database
From the project root:
```powershell
cd infrastructure
docker compose up -d
```
For a fresh local database, the compose file uses `campusfind_user` / `change_me`. If you already have a PostgreSQL volume from your earlier work, its existing password remains in effect; update `backend/.env` to match it rather than deleting the volume.

Enable pgvector once:
```powershell
docker exec -it campusfind-postgres psql -U campusfind_user -d campusfind_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## 2. Backend
Open another terminal:
```powershell
cd backend
py -3.10 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```
Edit `backend/.env` and set DATABASE_URL to your database password. Set a strong random SECRET_KEY.
Start:
```powershell
python -m uvicorn app.main:app --reload
```
Swagger: http://127.0.0.1:8000/docs

## 3. Frontend
The `frontend` folder contains starter Angular source files. Install Node.js LTS, then from `frontend` generate the Angular workspace:
```powershell
npx @angular/cli new campusfind-frontend --directory . --routing --style css
```
If the CLI asks to overwrite existing starter files, preserve the supplied `src/app` and `src/main.ts` files or copy them back after generation. Add Bootstrap (or keep the CDN import in `src/styles.css`), then replace generated `src/app/app.component.ts`, `src/app/services/item.service.ts`, and `src/main.ts` with the supplied files. Run:
```powershell
npm install
ng serve
```
Open http://localhost:4200

## API endpoints
- POST /auth/register
- POST /auth/login
- POST /items/
- GET /items/
- GET /items/search
- GET /items/{item_id}
- PUT /items/{item_id}
- DELETE /items/{item_id}

## Example item
```json
{
  "title": "Black Dell Laptop",
  "description": "Black Dell laptop with a blue sticker near the college library.",
  "item_type": "lost",
  "category": "Electronics",
  "location": "College Library",
  "event_date": "2026-11-04T10:30:00",
  "image_url": null
}
```
