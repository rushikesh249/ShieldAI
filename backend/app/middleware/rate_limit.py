from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time

# Simple in-memory rate limiting dictionary
# Format: { "ip_address": { "count": int, "reset_time": float } }
RATE_LIMIT_STORE = {}

# 10 requests per minute per IP
MAX_REQUESTS = 10
WINDOW_SECONDS = 60

class RateLimitingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Initialize or reset the store for this IP
        if client_ip not in RATE_LIMIT_STORE:
            RATE_LIMIT_STORE[client_ip] = {"count": 1, "reset_time": current_time + WINDOW_SECONDS}
        else:
            record = RATE_LIMIT_STORE[client_ip]
            if current_time > record["reset_time"]:
                # Reset window
                RATE_LIMIT_STORE[client_ip] = {"count": 1, "reset_time": current_time + WINDOW_SECONDS}
            else:
                if record["count"] >= MAX_REQUESTS:
                    return JSONResponse(
                        status_code=429,
                        content={"success": False, "message": "Too Many Requests", "errors": ["Rate limit exceeded. Please try again later."]}
                    )
                record["count"] += 1
                
        response = await call_next(request)
        return response
