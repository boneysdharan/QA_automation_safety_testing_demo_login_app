from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from detoxify import Detoxify
import uvicorn
import json

app = FastAPI(title="Task_1 API")

# Allow all origins for Postman/UI tests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Detoxify model at startup
model = Detoxify("original")

# Dummy users
USERS = {"admin": "password123"}

# LOGIN
@app.post("/api/login")
async def login(request: Request):
    try:
        if request.headers.get("content-type") != "application/json":
            raise HTTPException(status_code=415, detail="Unsupported Media Type: JSON required")
        data = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    username = data.get("username", "")
    password = data.get("password", "")

    if not username:
        raise HTTPException(status_code=400, detail="Username required")
    if not password:
        raise HTTPException(status_code=400, detail="Password required")

    if username not in USERS:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if USERS[username] == password:
        return {"status": "success", "token": "fake-jwt-token"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# PROTECTED
@app.get("/api/protected")
async def protected(request: Request):
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if auth_header == "Bearer fake-jwt-token":
        return {"message": "You have access to protected data"}

    # simulate expired/invalid token handling
    if "expired" in auth_header.lower():
        raise HTTPException(status_code=401, detail="Token expired")

    raise HTTPException(status_code=401, detail="Invalid or expired token")

# MODERATION
@app.post("/api/moderate")
async def moderate(request: Request):
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Invalid payload")

    text = body.get("text")
    if text is None:
        raise HTTPException(status_code=400, detail="Missing 'text' field")
    if not isinstance(text, str):
        raise HTTPException(status_code=400, detail="Text must be a string")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text required")

    try:
        results = model.predict(text)
        clean_results = {k: float(v) for k, v in results.items()}
        toxicity_label = "toxic" if clean_results["toxicity"] > 0.5 else "non-toxic"

        return {
            "text": text,
            "toxicity": toxicity_label,
            "toxicity_scores": clean_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Moderation failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)