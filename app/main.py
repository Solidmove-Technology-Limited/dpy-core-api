from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine, Base
from app.routes import auth, wallet, transactions, users

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DPY Core API",
    description="Core API for DPY engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "DPY Core API is running",
        "status": "operational",
        "company": "SOLIDMOVE TECHNOLOGY LIMITED"
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(users.router, prefix="/users", tags=["users"])
