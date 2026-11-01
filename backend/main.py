"""
FastAPI main application
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from routers import sentiment, companies, realtime, analyze
from database import engine, Base

REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests served by the API",
    ["method", "endpoint"],
)

app = FastAPI(
    title="IPO Sentiment Analysis API",
    description="Real-time sentiment analysis for any Indian stock — scrape, score, suggest",
    version="1.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (analyze before companies/{symbol} paths where needed)
app.include_router(analyze.router)
app.include_router(sentiment.router)
app.include_router(companies.router)
app.include_router(realtime.router)

@app.middleware("http")
async def count_requests(request: Request, call_next):
    response = await call_next(request)
    if request.url.path != "/metrics":
        REQUESTS.labels(request.method, request.url.path).inc()
    return response


@app.on_event("startup")
async def startup():
    """Initialize database tables. Probes stay up if Postgres is still starting."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        pass

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IPO Sentiment Analysis API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/metrics")
def metrics():
    """Prometheus scrape target."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

