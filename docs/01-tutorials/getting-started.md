# Getting Started

Follow these steps to run the app locally. This mirrors the README quickstart but includes the `mise` trust step.

## 1) Install prerequisites

- Python 3.11+
- PostgreSQL 15+

## 2) (Optional) Trust repo tool versions

This repo uses `mise.toml` to pin tool versions. If you see a warning about an untrusted config, trust it once from the repo root:

```bash
mise trust
```

If you prefer not to use mise, you can ignore this warning.

## 3) Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4) Configure environment variables

```bash
export DJANGO_SECRET_KEY="dev-secret-key"
export DJANGO_DEBUG=True
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
export POSTGRES_DB=consultantpro
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 5) Run migrations

```bash
cd src
python manage.py migrate
```

## 6) Start the server

```bash
python manage.py runserver 0.0.0.0:8000
```

## 7) Confirm it is running

- API Docs: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## Troubleshooting

### `DJANGO_SECRET_KEY environment variable is required`

Set the environment variable in step 4 and re-run the server.

### `mise` config not trusted

Run `mise trust` from the repo root or ignore the warning.
