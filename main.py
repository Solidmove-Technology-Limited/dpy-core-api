from fastapi import FastAPI
import os

app = FastAPI(title="DPY Core API")

@app.get("/")
def root():
    return {"message": "Pyramide DPY is live!", "company": "SolidMove Technology Limited"}

@app.get("/api/v1/health")
def health():
    return {"status": "operational", "service": "pyramide"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
