from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.db import engine, Base
from app.routes import auth, wallet, transactions, users

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DPY Core API",
    description="Core API for DPY engine",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(users.router, prefix="/users", tags=["users"])

@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        conn.commit()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
