# App package
try:
    from main import app
except ImportError:
    # This handles cases where main.py might not be in the path during early initialization
    pass
