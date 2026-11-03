import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.db import engine, Base
from app.routes import auth, wallet, transactions, users, chat

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DPY Core API",
    description="Core API for DPY engine",
    version="1.1.0"
)

# CORS: explicit origin allowlist. The previous configuration paired
# allow_origins=["*"] with allow_credentials=True, which browsers reject and
# which exposes credentialed responses to any origin.
_origins = [o.strip() for o in os.getenv("DPY_ALLOWED_ORIGINS", "").split(",") if o.strip()]
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

_hosts = [h.strip() for h in os.getenv("DPY_ALLOWED_HOSTS", "").split(",") if h.strip()]
if _hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=_hosts)


@app.get("/")
async def root():
    return {
        "message": "DPY Core API is running",
        "status": "operational",
        "company": "SOLIDMOVE TECHNOLOGY LIMITED"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "model_configured": bool(os.getenv("DPY_MODEL_API_KEY")),
        "version": app.version,
    }


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(chat.router, tags=["chat"])
