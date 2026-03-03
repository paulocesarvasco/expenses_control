# Expenses Control

Flask application to register and view domestic expenses, with:

- Web/API endpoints under `/v1`
- SQLAlchemy models for shopping trips, products, categories, and purchased items
- Flask CLI commands for database setup and data inspection

## Requirements

- Python `3.13+`
- [Poetry](https://python-poetry.org/) `2.x`

## 1. Install dependencies

```bash
poetry install
```

## 2. Configure environment variables

The app reads environment variables from `.env` (via `python-dotenv`).

Create a `.env` file in the project root:

```bash
cat > .env << 'EOF'
DB_URL=sqlite:///expenses.db
EOF
```

`DB_URL` can also point to MySQL (example: `mysql+pymysql://user:password@localhost/expenses_db`).

## 3. Initialize database tables

```bash
poetry run flask --app app:create_app init-db
```

## 4. Run the app locally

```bash
poetry run flask --app app:create_app --debug run
```

By default, Flask serves at: `http://127.0.0.1:5000`

Production (WSGI) run command:

```bash
poetry run gunicorn -c gunicorn.conf.py 'app:create_app()'
```

Gunicorn settings are centralized in `gunicorn.conf.py` and can be overridden with env vars like:
`GUNICORN_BIND`, `GUNICORN_WORKERS`, `GUNICORN_THREADS`, `GUNICORN_TIMEOUT`.

## Run with Docker + PostgreSQL

The repository now includes `Dockerfile` and `docker-compose.yml` with:

- `app` service (Flask)
- `db` service (`postgres:16-alpine`)

Start the full stack:

```bash
docker compose up --build
```

The app container starts with Gunicorn (WSGI) in production mode.

App URL:

- `http://127.0.0.1:5000/v1/`

The app container uses this SQLAlchemy URL:

- `postgresql+psycopg://expenses:expenses@db:5432/expenses`

Stop and remove containers:

```bash
docker compose down
```

## 5. Main routes

- `GET /v1/` - base page
- `GET /v1/product/list` - list products (JSON)
- `GET /v1/purchase/register_form` - purchase registration page
- `POST /v1/purchase/save` - save a purchase (JSON body)
- `GET /v1/purchase/search` - search purchases by date range (`start`, `end`)

## Useful CLI commands

```bash
poetry run flask --app app:create_app list-categories
poetry run flask --app app:create_app list-products
poetry run flask --app app:create_app list-items
poetry run flask --app app:create_app register-product
poetry run flask --app app:create_app edit-shopping
```

To list all available routes:

```bash
poetry run flask --app app:create_app routes
```

## Notes

- Logs are written to the `logs/` directory (`debug.log`, `error.log`, `views.log`).
- The `save purchase` flow requires products to exist in the database first.
