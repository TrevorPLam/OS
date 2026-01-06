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

Create a `.env` file in the project root and add the following variables. The application will load these automatically. **Note:** Replace `dev-secret-key` with a unique key generated using the command in the comment above.

```bash
# .env
DJANGO_SECRET_KEY="dev-secret-key" # Replace with a real secret key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=consultantpro
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

## 5) Run migrations

```bash
python src/manage.py migrate

## 7) Confirm it is running

- API Docs: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## Troubleshooting

### `DJANGO_SECRET_KEY environment variable is required`

Set the environment variable in step 4 and re-run the server.

### `mise` config not trusted

Run `mise trust` from the repo root or ignore the warning.
