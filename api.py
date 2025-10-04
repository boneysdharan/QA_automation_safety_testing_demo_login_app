from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from detoxify import Detoxify
import uvicorn

app = FastAPI(title="Task_1 API")

# Allow frontend & Postman
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Detoxify model once at startup
model = Detoxify("original")

# Dummy users
USERS = {"admin": "password123"}

# LOGIN
@app.post("/api/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username", "")
    password = data.get("password", "")

    if not username:
        raise HTTPException(status_code=400, detail="Username required")
    if not password:
        raise HTTPException(status_code=400, detail="Password required")

    if USERS.get(username) == password:
        return {"status": "success", "token": "fake-jwt-token"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# PROTECTED
@app.get("/api/protected")
async def protected(request: Request):
    auth_header = request.headers.get("Authorization")
    if auth_header != "Bearer fake-jwt-token":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"message": "You have access to protected data"}

# MODERATION
@app.post("/api/moderate")
async def moderate(request: Request):
    body = await request.json()
    text = body.get("text", "")

    if not text:
        raise HTTPException(status_code=400, detail="Text required")

    try:
        results = model.predict(text)
        # Convert numpy.float32 → Python float
        clean_results = {k: float(v) for k, v in results.items()}

        # Add top-level toxicity label
        toxicity_label = "toxic" if clean_results["toxicity"] > 0.5 else "non-toxic"

        return {
            "text": text,
            "toxicity": toxicity_label,     # <-- fix for pytest
            "toxicity_scores": clean_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Moderation failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
