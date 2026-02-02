
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import os

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    enabled=os.getenv("TESTING", "false").lower() != "true"
)

def init_limiter(app):
    """Initialize limiter with app"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
