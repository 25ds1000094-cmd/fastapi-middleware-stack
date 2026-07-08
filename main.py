from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time
from collections import defaultdict

app = FastAPI()

EMAIL = "25ds1000094@ds.study.iitm.ac.in"

# Assigned CORS origins
ALLOWED_ORIGINS = [
    "https://app-mov4li.example.com",
    "https://exam.sanand.workers.dev"
]

# Assigned rate limit
RATE_LIMIT = 10       # requests
WINDOW = 10           # seconds

# Store timestamps per client ID
client_requests = defaultdict(list)


# -----------------------------
# Middleware 1: Request Context
# -----------------------------
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    # Always echo request ID in response header
    response.headers["X-Request-ID"] = request_id

    return response


# -----------------------------
# Middleware 2: Rate Limiter
# -----------------------------
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id", "unknown")

    now = time.time()

    # Remove requests outside the 10 second window
    client_requests[client_id] = [
        timestamp
        for timestamp in client_requests[client_id]
        if now - timestamp < WINDOW
    ]

    # Block after 10 requests
    if len(client_requests[client_id]) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

    client_requests[client_id].append(now)

    return await call_next(request)


# -----------------------------
# Middleware 3: CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Endpoint
# -----------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
