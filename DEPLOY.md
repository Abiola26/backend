Deployment notes
================


Recommended Gunicorn command
----------------------------

Prefer the top-level module path `main:app` (the repository root `main.py` re-exports `app`) because many PaaS platforms default to `main:app` and it's a simple, predictable entrypoint:

```
gunicorn main:app -k uvicorn.workers.UvicornWorker
```

Alternative (explicit package path)
-----------------------------------

If you prefer to point directly at the package module, use:

```
gunicorn app.main:app -k uvicorn.workers.UvicornWorker
```

Why both are supported
----------------------

- `main:app` is convenient for platform defaults and for cases where you want a single top-level launcher.
- `app.main:app` is explicit and avoids relying on a re-export; both are valid. The repository keeps a top-level `main.py` that re-exports `app` so either command works.

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
