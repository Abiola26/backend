# Gunicorn configuration file
import multiprocessing
import os

# Port and binding
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

# Worker configuration
worker_class = "uvicorn.workers.UvicornWorker"
# Limit workers to avoid memory/DB connection issues on small instances
workers = int(os.environ.get("GUNICORN_WORKERS", 2))
# If GUNICORN_WORKERS is not set, use a small default instead of scaling with CPU
if not os.environ.get("GUNICORN_WORKERS") and multiprocessing.cpu_count() > 1:
    workers = min(multiprocessing.cpu_count(), 4) # Max 4 by default

timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
