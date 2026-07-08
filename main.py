from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time
from collections import defaultdict

app = FastAPI()

EMAIL = "25ds1000094@ds.study.iitm.ac.in"

RATE_LIMIT = 10
WINDOW = 10

ALLOWED_ORIGINS = [
    "https://app-mov4li.example.com",
    "https://exam.sanand.workers.dev"
]

clients = defaultdict(list)


# -------------------------
# Request ID Middleware
# -------------------------
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID")

        if not request_id:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        # Echo request ID in response header
        response.headers["X-Request-ID"] = request_id

        return response


# -------------------------
# Rate Limit Middleware
# -------------------------
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_id = request.headers.get("X-Client-Id", "unknown")

        now = time.time()

        # Remove requests older than 10 seconds
        clients[client_id] = [
            t for t in clients[client_id]
            if now - t < WINDOW
        ]

        if len(clients[client_id]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )

        clients[client_id].append(now)

        return await call_next(request)


# -------------------------
# Add middleware
# -------------------------

# Custom middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)

# CORS must be outermost
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# -------------------------
# Endpoint
# -------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
