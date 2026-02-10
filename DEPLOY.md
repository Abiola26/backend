Deployment notes
================

Recommended Gunicorn command
----------------------------

When deploying to Render, Heroku, or other platforms that run `gunicorn`, use the explicit module path so the server can reliably find the ASGI application instance:

```
gunicorn app.main:app -k uvicorn.workers.UvicornWorker
```

Why this matters
-----------------

- Using `main:app` relies on a top-level `main.py` re-export which can be fragile if packaging changes. `app.main:app` points directly to the application factory module inside the package.

Required environment variables
------------------------------

- `SECRET_KEY` (required in production): set to a secure random value.
- `DATABASE_URL`: production database connection string (postgresql://...)
- Optional mail settings if you use email features:
  - `MAIL_USERNAME`
  - `MAIL_PASSWORD`
  - `MAIL_FROM`

Troubleshooting
---------------

- If you see `Failed to find attribute 'app' in 'main'`, ensure your Procfile or start command uses `app.main:app` or that `main.py` re-exports `app`.
- Ensure `SECRET_KEY` is set in the Render/Heroku environment to avoid JWT issues.
