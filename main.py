from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time
from collections import defaultdict

app = FastAPI()

EMAIL = "25ds1000094@ds.study.iitm.ac.inm"

# Assigned values
ALLOWED_ORIGIN = "https://app-mov4li.example.com"

RATE_LIMIT = 10
WINDOW = 10

# Store requests per client
client_requests = defaultdict(list)


# -----------------------------
# Middleware 1: Request Context
# -----------------------------
@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# -----------------------------
# Middleware 2: Rate Limiter
# -----------------------------
@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id", "unknown")

    now = time.time()

    # Remove old requests
    client_requests[client_id] = [
        t for t in client_requests[client_id]
        if now - t < WINDOW
    ]

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
    allow_origins=[
        "https://app-mov4li.example.com"
    ],
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
