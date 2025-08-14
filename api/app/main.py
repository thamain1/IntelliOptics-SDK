import os
import time
import uuid
from typing import Optional, Literal, List

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# ---------- Config ----------
API_TOKEN = os.getenv("INTELLOPTICS_API_TOKEN", "change-me")  # master/admin token
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Default to a local SQLite file under site dir; override with DB_URL if you switch to Postgres later
DB_URL = os.getenv("DB_URL", "sqlite:///data/app.db")

# Ensure data folder exists (works on Azure App Service since cwd is under /home/site/wwwroot)
os.makedirs("data", exist_ok=True)

app = FastAPI(title="IntelliOptics API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- DB ----------
engine: Engine = create_engine(DB_URL, future=True)

def init_db():
    with engine.begin() as con:
        # tokens
        con.execute(text("""
        CREATE TABLE IF NOT EXISTS tokens(
            token TEXT PRIMARY KEY,
            label TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1
        )
        """))
        # detectors
        con.execute(text("""
        CREATE TABLE IF NOT EXISTS detectors(
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            mode TEXT NOT NULL,
            query_text TEXT NOT NULL,
            threshold REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
        # image queries
        con.execute(text("""
        CREATE TABLE IF NOT EXISTS image_queries(
            id TEXT PRIMARY KEY,
            detector_id TEXT NOT NULL,
            answer TEXT NOT NULL,
            confidence REAL NOT NULL,
            latency_ms INTEGER,
            model_version TEXT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
        # feedback
        con.execute(text("""
        CREATE TABLE IF NOT EXISTS feedback(
            id TEXT PRIMARY KEY,
            image_query_id TEXT NOT NULL,
            correct_label TEXT NOT NULL,
            bboxes_json TEXT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))

init_db()

# ---------- Auth helpers ----------
def _get_bearer_from_headers(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return auth.split(" ", 1)[1].strip()

def require_bearer():
    """Dependency that accepts either the master API token or a user token from the DB."""
    async def _dep(request: Request):
        supplied = _get_bearer_from_headers(request)
        if supplied == API_TOKEN:
            return  # master token OK
        # Otherwise, check tokens table
        with engine.begin() as con:
            row = con.execute(
                text("SELECT token FROM tokens WHERE token = :t AND active = 1"),
                {"t": supplied},
            ).first()
        if not row:
            raise HTTPException(status_code=403, detail="Invalid token")
    return _dep

# ---------- Schemas ----------
AnswerLabel = Literal["YES", "NO", "COUNT", "UNCLEAR"]

class DetectorOut(BaseModel):
    id: str
    name: str
    mode: Literal["binary", "count", "custom"]
    query_text: str
    threshold: float
    status: str = "active"

class DetectorCreate(BaseModel):
    name: str
    mode: Literal["binary", "count", "custom"]
    query_text: str
    threshold: float = 0.75

class AnswerOut(BaseModel):
    image_query_id: str
    answer: AnswerLabel
    confidence: float
    latency_ms: Optional[int] = None
    model_version: Optional[str] = "demo-v0"

class TokenCreate(BaseModel):
    label: Optional[str] = None

class TokenOut(BaseModel):
    token: str
    label: Optional[str] = None
    active: bool = True
    created_at: Optional[str] = None

# ---------- Routes ----------
@app.get("/healthz")
def healthz():
    return {"status": "ok", "version": app.version}

# --- Token management (admin/master only for issuance & listing) ---
@app.post("/v1/tokens", response_model=TokenOut, dependencies=[Depends(require_bearer())])
def create_token(payload: TokenCreate, request: Request):
    # Only allow the master token to mint new tokens
    if _get_bearer_from_headers(request) != API_TOKEN:
        raise HTTPException(403, "Only master token may create tokens")

    new_token = uuid.uuid4().hex  # 32-char token
    with engine.begin() as con:
        con.execute(
            text("INSERT INTO tokens(token, label, active) VALUES(:t, :label, 1)"),
            {"t": new_token, "label": payload.label},
        )
        row = con.execute(
            text("SELECT token, label, active, created_at FROM tokens WHERE token=:t"),
            {"t": new_token},
        ).mappings().one()
    return {"token": row["token"], "label": row["label"], "active": bool(row["active"]), "created_at": str(row["created_at"])}

@app.get("/v1/tokens", response_model=List[TokenOut], dependencies=[Depends(require_bearer())])
def list_tokens(request: Request):
    if _get_bearer_from_headers(request) != API_TOKEN:
        raise HTTPException(403, "Only master token may list tokens")

    with engine.begin() as con:
        rows = con.execute(text("SELECT token, label, active, created_at FROM tokens ORDER BY created_at DESC")).mappings().all()
    return [
        {"token": r["token"], "label": r["label"], "active": bool(r["active"]), "created_at": str(r["created_at"])}
        for r in rows
    ]

@app.delete("/v1/tokens/{token}", dependencies=[Depends(require_bearer())])
def revoke_token(token: str, request: Request):
    if _get_bearer_from_headers(request) != API_TOKEN:
        raise HTTPException(403, "Only master token may revoke tokens")
    with engine.begin() as con:
        res = con.execute(text("UPDATE tokens SET active=0 WHERE token=:t"), {"t": token})
    if res.rowcount == 0:
        raise HTTPException(404, "Token not found")
    return {"status": "revoked", "token": token}

# --- Detectors ---
@app.post("/v1/detectors", response_model=DetectorOut, dependencies=[Depends(require_bearer())])
def create_detector(payload: DetectorCreate):
    det_id = str(uuid.uuid4())
    with engine.begin() as con:
        con.execute(text("""
            INSERT INTO detectors(id,name,mode,query_text,threshold,status)
            VALUES(:id,:name,:mode,:query_text,:threshold,'active')
        """), dict(id=det_id, name=payload.name, mode=payload.mode,
                   query_text=payload.query_text, threshold=payload.threshold))
        row = con.execute(text(
            "SELECT id,name,mode,query_text,threshold,status FROM detectors WHERE id=:id"
        ), dict(id=det_id)).mappings().one()
    return row

@app.get("/v1/detectors/{detector_id}", response_model=DetectorOut, dependencies=[Depends(require_bearer())])
def get_detector(detector_id: str):
    with engine.begin() as con:
        row = con.execute(text(
            "SELECT id,name,mode,query_text,threshold,status FROM detectors WHERE id=:id"
        ), dict(id=detector_id)).mappings().first()
    if not row:
        raise HTTPException(404, "Detector not found")
    return row

# --- Image queries (multipart) ---
@app.post("/v1/image-queries", response_model=AnswerOut, dependencies=[Depends(require_bearer())])
async def image_query(
    detector_id: str = Form(...),
    wait: bool = Form(True),
    image: Optional[UploadFile] = File(None),
):
    start = time.time()
    answer: AnswerLabel = "UNCLEAR"
    conf = 0.50
    try:
        if image and "yes" in (image.filename or "").lower():
            answer, conf = "YES", 0.92
        elif image and "no" in (image.filename or "").lower():
            answer, conf = "NO", 0.93
    except Exception:
        pass

    iq_id = str(uuid.uuid4())
    latency = int((time.time() - start) * 1000)
    with engine.begin() as con:
        con.execute(text("""
            INSERT INTO image_queries(id, detector_id, answer, confidence, latency_ms, model_version)
            VALUES(:id,:detector_id,:answer,:confidence,:latency,:mv)
        """), dict(id=iq_id, detector_id=detector_id, answer=answer,
                   confidence=conf, latency=latency, mv="demo-v0"))

    return {"image_query_id": iq_id, "answer": answer, "confidence": conf,
            "latency_ms": latency, "model_version": "demo-v0"}

# --- Image queries (JSON) ---
class ImageQueryJson(BaseModel):
    detector_id: str
    image: Optional[str] = None
    wait: bool = True

@app.post("/v1/image-queries-json", response_model=AnswerOut, dependencies=[Depends(require_bearer())])
def image_query_json(payload: ImageQueryJson):
    start = time.time()
    answer, conf = ("YES", 0.91) if payload.image and "yes" in payload.image.lower() else ("NO", 0.91)
    iq_id = str(uuid.uuid4())
    latency = int((time.time() - start) * 1000)
    with engine.begin() as con:
        con.execute(text("""
            INSERT INTO image_queries(id, detector_id, answer, confidence, latency_ms, model_version)
            VALUES(:id,:detector_id,:answer,:confidence,:latency,:mv)
        """), dict(id=iq_id, detector_id=payload.detector_id, answer=answer,
                   confidence=conf, latency=latency, mv="demo-v0"))
    return {"image_query_id": iq_id, "answer": answer, "confidence": conf,
            "latency_ms": latency, "model_version": "demo-v0"}

@app.get("/v1/image-queries/{iq_id}", response_model=AnswerOut, dependencies=[Depends(require_bearer())])
def get_image_query(iq_id: str):
    with engine.begin() as con:
        row = con.execute(text("""
            SELECT id as image_query_id, answer, confidence, latency_ms, model_version
            FROM image_queries WHERE id=:id
        """), dict(id=iq_id)).mappings().first()
    if not row:
        raise HTTPException(404, "Not found")
    return row

# --- Feedback ---
class FeedbackIn(BaseModel):
    image_query_id: str
    correct_label: AnswerLabel
    bboxes: Optional[list[dict]] = None

@app.post("/v1/feedback", dependencies=[Depends(require_bearer())])
def feedback(payload: FeedbackIn):
    fb_id = str(uuid.uuid4())
    with engine.begin() as con:
        con.execute(text("""
            INSERT INTO feedback(id, image_query_id, correct_label, bboxes_json)
            VALUES(:id,:iq,:label,:bboxes)
        """), dict(id=fb_id, iq=payload.image_query_id, label=payload.correct_label,
                   bboxes=None if payload.bboxes is None else str(payload.bboxes)))
    return {"status": "ok", "feedback_id": fb_id}
