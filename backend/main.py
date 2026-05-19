from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from backend.api.v1 import runtime, feedback, prompts, iterations, evaluations
from backend.db.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (replaced by Alembic in prod)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="APIS Engine",
    description="Adaptive Prompt Intelligence System — Runtime, Feedback, and Admin APIs",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(runtime.router,  prefix="/api/v1/runtime",  tags=["Runtime"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])
app.include_router(prompts.router,  prefix="/api/v1",          tags=["Admin — Prompts"])
app.include_router(iterations.router, prefix="/api/v1",          tags=["Admin — Iterations"])
app.include_router(evaluations.router, prefix="/api/v1",          tags=["Admin — Evaluations"])


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )
