from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time
from collections import defaultdict

app = FastAPI()

EMAIL = "25ds1000094@ds.study.iitm.ac.in"

ALLOWED_ORIGINS=[
        "https://app-mov4li.example.com",
        "https://exam.sanand.workers.dev"
    ],

RATE_LIMIT = 10
WINDOW = 10

requests_by_client = defaultdict(list)


# Request Context Middleware
@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if request_id is None:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# Rate Limit Middleware
@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id", "default")

    now = time.time()

    requests_by_client[client_id] = [
        t for t in requests_by_client[client_id]
        if now - t < WINDOW
    ]

    if len(requests_by_client[client_id]) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

    requests_by_client[client_id].append(now)

    return await call_next(request)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
