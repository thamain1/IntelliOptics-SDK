#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="intellioptics-oneclick"

if [ -d "$REPO_DIR" ]; then
  echo "[info] Directory '$REPO_DIR' already exists. Remove it or choose another location."
  exit 1
fi

mkdir -p "$REPO_DIR"
cd "$REPO_DIR"

# --- helper
w() { # w <path> ; then feed heredoc
  local p="$1"
  mkdir -p "$(dirname "$p")"
  cat > "$p"
}

# --- root files
w .gitignore <<'EOF'
.env
__pycache__/
*.pyc
*.pyo
*.pyd
*.log
*.sqlite3
.DS_Store
EOF

w README.md <<'EOF'
# IntelliOptics One‑and‑Done Stack

This repo installs a production‑ready IntelliOptics backend (FastAPI) and a queue‑driven worker (ACI by default), complete with Human‑in‑the‑Loop endpoints. Flip to AKS + Managed Identity + Key Vault later without code changes.

## Quickstart
1. Copy `.env.example` to `.env` and fill values (do **not** commit `.env`).
2. Run `bash deploy/install.sh`.
3. The script provisions core Azure resources, builds/pushes images to ACR, deploys the API to **App Service for Containers** and the worker to **Azure Container Instances**.

## Flip to secure (later)
- Replace Service Bus connection strings with **Managed Identity**.
- Move to **AKS** or **Container Apps**.
- Mount secrets from **Key Vault** (CSI or App Service references).
- Enable Application Insights.
EOF

w .env.example <<'EOF'
# Azure core
AZ_SUBSCRIPTION_ID=
AZ_TENANT_ID=
AZ_RESOURCE_GROUP=io-rg
AZ_LOCATION=eastus

# ACR
ACR_NAME=
ACR_LOGIN_SERVER=
ACR_USERNAME=
ACR_PASSWORD=

# Service Bus (now: conn string OR namespace; later: MI)
SERVICE_BUS_CONN=
AZ_SB_NAMESPACE=
SB_QUEUE_LISTEN=image-queries
SB_QUEUE_SEND=inference-results
SB_QUEUE_FEEDBACK=feedback

# Storage (optional for uploads)
AZ_BLOB_ACCOUNT=
AZ_BLOB_CONTAINER=images

# Postgres (either DSN or discrete fields)
POSTGRES_DSN=
PG_HOST=
PG_DB=intellioptics
PG_USER=
PG_PASSWORD=
PG_SSLMODE=require

# IntelliOptics
INTELLOPTICS_API_BASE=
INTELLIOPTICS_API_TOKEN=

# API
ALLOWED_ORIGINS=*
API_BASE_PATH=/v1

# Images
IMAGE_NAME=io-worker
IMAGE_TAG=latest

# App Service API
API_PLAN=io-api-plan
WEBAPP=io-api

# Tuning
DEFAULT_CONFIDENCE=0.9
DEFAULT_TIMEOUT=30
EOF

# --- deploy scripts
w deploy/common.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] || { echo "Missing .env at repo root"; exit 2; }
# shellcheck disable=SC1091
set -a; . ./.env; set +a
: "${AZ_RESOURCE_GROUP:?}"; : "${AZ_LOCATION:?}"; : "${ACR_LOGIN_SERVER:?}"; : "${INTELLIOPTICS_API_TOKEN:?}"
AZR=${AZ_RESOURCE_GROUP}; LOC=${AZ_LOCATION}
ACR=${ACR_LOGIN_SERVER%%.*}
SB_QUEUE_LISTEN=${SB_QUEUE_LISTEN:-image-queries}
SB_QUEUE_SEND=${SB_QUEUE_SEND:-inference-results}
SB_QUEUE_FEEDBACK=${SB_QUEUE_FEEDBACK:-feedback}
EOF
chmod +x deploy/common.sh

w deploy/provision.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/common.sh"

az group create -n "$AZR" -l "$LOC" >/dev/null

# ACR (create if missing)
az acr show -n "$ACR" >/dev/null 2>&1 || az acr create -n "$ACR" -g "$AZR" -l "$LOC" --sku Basic >/dev/null

# Service Bus
if [ -n "${SERVICE_BUS_CONN:-}" ]; then
  echo "[info] Using existing Service Bus connection string"
else
  : "${AZ_SB_NAMESPACE:?Set AZ_SB_NAMESPACE or SERVICE_BUS_CONN}"
  az servicebus namespace show -g "$AZR" -n "$AZ_SB_NAMESPACE" >/dev/null 2>&1 || \
    az servicebus namespace create -g "$AZR" -n "$AZ_SB_NAMESPACE" -l "$LOC" --sku Standard >/dev/null
  for q in "$SB_QUEUE_LISTEN" "$SB_QUEUE_SEND" "$SB_QUEUE_FEEDBACK"; do
    az servicebus queue create -g "$AZR" --namespace-name "$AZ_SB_NAMESPACE" -n "$q" >/dev/null || true
  done
fi

# Storage
if [ -n "${AZ_BLOB_ACCOUNT:-}" ]; then
  az storage account show -g "$AZR" -n "$AZ_BLOB_ACCOUNT" >/dev/null 2>&1 || \
    az storage account create -g "$AZR" -n "$AZ_BLOB_ACCOUNT" -l "$LOC" --sku Standard_LRS >/dev/null
  az storage container create --account-name "$AZ_BLOB_ACCOUNT" -n "${AZ_BLOB_CONTAINER:-images}" >/dev/null || true
fi

# Postgres: assume provided externally
EOF
chmod +x deploy/provision.sh

w deploy/appservice-api.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/common.sh"

IMG="$ACR_LOGIN_SERVER/intellioptics-api:latest"

az acr login --name "$ACR" >/dev/null
( cd backend && docker build -t "$IMG" . && docker push "$IMG" )

API_PLAN=${API_PLAN:-io-api-plan}
WEBAPP=${WEBAPP:-io-api}

az appservice plan show -g "$AZR" -n "$API_PLAN" >/dev/null 2>&1 || \
  az appservice plan create -g "$AZR" -n "$API_PLAN" -l "$LOC" --is-linux --sku P1v3 >/dev/null

az webapp show -g "$AZR" -n "$WEBAPP" >/dev/null 2>&1 || \
  az webapp create -g "$AZR" -p "$API_PLAN" -n "$WEBAPP" -i "$IMG" >/dev/null

az webapp config appsettings set -g "$AZR" -n "$WEBAPP" --settings \
  AZ_SB_NAMESPACE=${AZ_SB_NAMESPACE:-} \
  AZ_SB_CONN_STR=${SERVICE_BUS_CONN:-} \
  AZ_BLOB_ACCOUNT=${AZ_BLOB_ACCOUNT:-} \
  AZ_BLOB_CONTAINER=${AZ_BLOB_CONTAINER:-images} \
  PG_HOST=${PG_HOST:-} PG_DB=${PG_DB:-intellioptics} PG_USER=${PG_USER:-} PG_PASSWORD=${PG_PASSWORD:-${PG_PASS:-}} PG_SSLMODE=${PG_SSLMODE:-require} \
  POSTGRES_DSN=${POSTGRES_DSN:-} \
  INTELLIOPTICS_API_TOKEN=${INTELLIOPTICS_API_TOKEN:-${INTELLOPTICS_API_TOKEN:-}} \
  INTELLIOPTICS_ENDPOINT=${INTELLIOPTICS_ENDPOINT:-${INTELLOPTICS_API_BASE:-}} \
  SB_QUEUE_LISTEN=${SB_QUEUE_LISTEN} SB_QUEUE_SEND=${SB_QUEUE_SEND} SB_QUEUE_FEEDBACK=${SB_QUEUE_FEEDBACK} \
  API_BASE_PATH=${API_BASE_PATH:-/v1} ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-*} >/dev/null

HOST=$(az webapp show -g "$AZR" -n "$WEBAPP" --query defaultHostName -o tsv)
echo "API URL: https://$HOST"
EOF
chmod +x deploy/appservice-api.sh

w deploy/aci-worker.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
. "$DIR/common.sh"

IMG="$ACR_LOGIN_SERVER/${IMAGE_NAME}:${IMAGE_TAG}"

az acr login --name "$ACR" >/dev/null
( cd worker-shim && docker build -t "$IMG" . && docker push "$IMG" )

ACI_NAME=${ACI_NAME:-io-worker}
ENVVARS=(
  "SB_QUEUE_LISTEN=${SB_QUEUE_LISTEN}"
  "SB_QUEUE_SEND=${SB_QUEUE_SEND}"
  "INTELLIOPTICS_API_TOKEN=${INTELLIOPTICS_API_TOKEN:-${INTELLOPTICS_API_TOKEN}}"
  "INTELLIOPTICS_ENDPOINT=${INTELLIOPTICS_ENDPOINT:-${INTELLOPTICS_API_BASE:-}}"
  "DEFAULT_CONFIDENCE=${DEFAULT_CONFIDENCE:-0.9}"
  "DEFAULT_TIMEOUT=${DEFAULT_TIMEOUT:-30}"
)
[ -n "${SERVICE_BUS_CONN:-}" ] && ENVVARS+=("SERVICE_BUS_CONN=$SERVICE_BUS_CONN")
[ -n "${AZ_SB_NAMESPACE:-}" ] && ENVVARS+=("AZ_SB_NAMESPACE=$AZ_SB_NAMESPACE")
[ -n "${POSTGRES_DSN:-}" ] && ENVVARS+=("POSTGRES_DSN=$POSTGRES_DSN")
[ -n "${PG_HOST:-}" ] && ENVVARS+=("PG_HOST=$PG_HOST" "PG_DB=${PG_DB:-intellioptics}" "PG_USER=$PG_USER" "PG_PASSWORD=$PG_PASSWORD" "PG_SSLMODE=${PG_SSLMODE:-require}")

az container create \
  -g "$AZR" -n "$ACI_NAME" -l "$LOC" \
  --image "$IMG" \
  --restart-policy Always \
  --cpu ${ACI_CPU:-1} --memory ${ACI_MEM_GB:-2} \
  --assign-identity \
  $(printf -- "--environment-variables %s " "${ENVVARS[@]}")

az container logs -g "$AZR" -n "$ACI_NAME" --follow || true
EOF
chmod +x deploy/aci-worker.sh

w deploy/install.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
"$DIR/provision.sh"
"$DIR/appservice-api.sh"
"$DIR/aci-worker.sh"
EOF
chmod +x deploy/install.sh

w deploy/install.ps1 <<'EOF'
# Runs the one-click installer from PowerShell (requires WSL or bash)
bash ./deploy/install.sh
EOF

# --- backend
w backend/Dockerfile <<'EOF'
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY app /app/app

RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic sqlalchemy psycopg[binary] \
    azure-identity azure-servicebus azure-storage-blob httpx intellioptics-sdk-python

EXPOSE 8080
CMD ["uvicorn", "app.main:create_app", "--host", "0.0.0.0", "--port", "8080"]
EOF

w backend/app/__init__.py <<'EOF'
# empty
EOF

w backend/app/config.py <<'EOF'
from pydantic import BaseModel
import os

class Settings(BaseModel):
    api_base_path: str = os.getenv("API_BASE_PATH", "/v1")
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "*")

    # IntelliOptics
    io_token: str | None = os.getenv("INTELLIOPTICS_API_TOKEN") or os.getenv("INTELLOPTICS_API_TOKEN")
    io_endpoint: str | None = os.getenv("INTELLIOPTICS_ENDPOINT") or os.getenv("INTELLOPTICS_API_BASE")

    # Service Bus
    sb_namespace: str | None = os.getenv("AZ_SB_NAMESPACE")
    sb_conn_str: str | None = os.getenv("AZ_SB_CONN_STR") or os.getenv("SERVICE_BUS_CONN")
    sb_image_queue: str = os.getenv("SB_QUEUE_LISTEN", "image-queries")
    sb_results_queue: str = os.getenv("SB_QUEUE_SEND", "inference-results")
    sb_feedback_queue: str = os.getenv("SB_QUEUE_FEEDBACK", "feedback")

    # Storage
    blob_account: str = os.getenv("AZ_BLOB_ACCOUNT", "")
    blob_container: str = os.getenv("AZ_BLOB_CONTAINER", "images")
    blob_conn_str: str | None = os.getenv("AZ_BLOB_CONN_STR")

    # Postgres
    pg_dsn: str | None = os.getenv("POSTGRES_DSN")
    pg_host: str = os.getenv("PG_HOST", "localhost")
    pg_db: str = os.getenv("PG_DB", "intellioptics")
    pg_user: str = os.getenv("PG_USER", "postgres")
    pg_password: str = os.getenv("PG_PASSWORD", "")
    pg_sslmode: str = os.getenv("PG_SSLMODE", "require")

settings = Settings()
EOF

w backend/app/db.py <<'EOF'
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

if settings.pg_dsn:
    conn_str = settings.pg_dsn
else:
    conn_str = (
        f"postgresql+psycopg://{settings.pg_user}:{settings.pg_password}"
        f"@{settings.pg_host}/{settings.pg_db}?sslmode={settings.pg_sslmode}"
    )

engine = create_engine(conn_str, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

with engine.connect() as c:
    c.execute(text("SELECT 1"))
EOF

w backend/app/migrations.py <<'EOF'
from sqlalchemy import text
from .db import engine

DDL = [
    """
    CREATE TABLE IF NOT EXISTS image_queries (
        id TEXT PRIMARY KEY,
        detector_id TEXT,
        blob_url TEXT,
        status TEXT,
        label TEXT,
        confidence DOUBLE PRECISION,
        result_type TEXT,
        count DOUBLE PRECISION,
        extra JSONB,
        done_processing BOOLEAN DEFAULT FALSE,
        human_label TEXT,
        human_confidence DOUBLE PRECISION,
        human_notes TEXT,
        human_user TEXT,
        human_labeled_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    """,
    """ALTER TABLE image_queries ADD COLUMN IF NOT EXISTS count DOUBLE PRECISION;""",
    """ALTER TABLE image_queries ADD COLUMN IF NOT EXISTS extra JSONB;""",
    """ALTER TABLE image_queries ADD COLUMN IF NOT EXISTS human_label TEXT;""",
    """ALTER TABLE image_queries ADD COLUMN IF NOT EXISTS human_confidence DOUBLE PRECISION;""",
    """ALTER TABLE image_queries ADD COLUMN IF NOT EXISTS human_notes TEXT;""",
    """ALTER TABLE image_queries ADD COLUMN IF NOT EXISTS human_user TEXT;""",
    """ALTER TABLE image_queries ADD COLUMN IF NOT EXISTS human_labeled_at TIMESTAMPTZ;""",
    """CREATE INDEX IF NOT EXISTS ix_image_queries_detector_id ON image_queries(detector_id);""",
    """CREATE INDEX IF NOT EXISTS ix_image_queries_created_at ON image_queries(created_at);""",
]

def migrate():
    with engine.begin() as conn:
        for stmt in DDL:
            conn.execute(text(stmt))
EOF

w backend/app/models.py <<'EOF'
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from .db import Base

class ImageQueryRow(Base):
    __tablename__ = "image_queries"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    detector_id: Mapped[str] = mapped_column(String, index=True)
    blob_url: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="SUBMITTED")
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    result_type: Mapped[str | None] = mapped_column(String, nullable=True)
    count: Mapped[float | None] = mapped_column(Float, nullable=True)
    extra = mapped_column(JSONB, nullable=True)
    done_processing: Mapped[bool] = mapped_column(Boolean, default=False)
    human_label: Mapped[str | None] = mapped_column(String, nullable=True)
    human_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    human_notes: Mapped[str | None] = mapped_column(String, nullable=True)
    human_user: Mapped[str | None] = mapped_column(String, nullable=True)
EOF

w backend/app/schemas.py <<'EOF'
from pydantic import BaseModel, Field

class SubmitQueryResponse(BaseModel):
    image_query_id: str
    status: str

class QueryStatusResponse(BaseModel):
    id: str
    status: str
    label: str | None = None
    confidence: float | None = None
    result_type: str | None = None
    count: float | None = None
    extra: dict | None = None

class HumanLabelRequest(BaseModel):
    label: str = Field(description="YES | NO | COUNT | UNCLEAR")
    confidence: float | None = None
    count: float | None = None
    notes: str | None = None
    user: str | None = None
    extra: dict | None = None
EOF

w backend/app/auth.py <<'EOF'
from fastapi import Request

async def require_auth(request: Request):
    # TODO: validate JWTs from Azure AD via JWKS in production
    return
EOF

w backend/app/queues/__init__.py <<'EOF'
# empty
EOF

w backend/app/queues/servicebus.py <<'EOF'
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.identity import DefaultAzureCredential
from ..config import settings

_cred = DefaultAzureCredential(exclude_shared_token_cache_credential=True)

if settings.sb_conn_str:
    _sb = ServiceBusClient.from_connection_string(settings.sb_conn_str)
else:
    if not settings.sb_namespace:
        raise RuntimeError("Provide SERVICE_BUS_CONN or AZ_SB_NAMESPACE")
    _sb = ServiceBusClient(fully_qualified_namespace=f"{settings.sb_namespace}.servicebus.windows.net", credential=_cred)

_img_sender = _sb.get_queue_sender(settings.sb_image_queue)
_res_sender = _sb.get_queue_sender(settings.sb_results_queue)
_fb_sender = _sb.get_queue_sender(settings.sb_feedback_queue)

async def enqueue_image_query(payload: dict):
    with _img_sender:
        _img_sender.send_messages(ServiceBusMessage(payload | {"kind": "image-query"}))

async def enqueue_result(payload: dict):
    with _res_sender:
        _res_sender.send_messages(ServiceBusMessage(payload | {"kind": "result"}))

async def enqueue_feedback(payload: dict):
    with _fb_sender:
        _fb_sender.send_messages(ServiceBusMessage(payload | {"kind": "feedback"}))
EOF

w backend/app/storage/__init__.py <<'EOF'
# empty
EOF

w backend/app/storage/blob.py <<'EOF'
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from ..config import settings
import uuid

_cred = DefaultAzureCredential(exclude_shared_token_cache_credential=True)

if settings.blob_conn_str:
    _svc = BlobServiceClient.from_connection_string(settings.blob_conn_str)
else:
    _svc = BlobServiceClient(f"https://{settings.blob_account}.blob.core.windows.net", credential=_cred)

container = _svc.get_container_client(settings.blob_container)
container.create_container(exist_ok=True)

async def save_image_bytes(data: bytes, content_type: str = "image/jpeg") -> str:
    blob_name = f"uploads/{uuid.uuid4()}.jpg"
    blob = container.get_blob_client(blob_name)
    blob.upload_blob(data, overwrite=False, content_type=content_type)
    return blob.url
EOF

w backend/app/clients/__init__.py <<'EOF'
# empty
EOF

w backend/app/clients/intellioptics_client.py <<'EOF'
from intellioptics import IntelliOptics, ExperimentalApi
from ..config import settings

_io = IntelliOptics(endpoint=settings.io_endpoint or None, api_token=settings.io_token)
_exp = ExperimentalApi(endpoint=settings.io_endpoint or None, api_token=settings.io_token)

def io_client() -> IntelliOptics:
    return _io

def exp_client() -> ExperimentalApi:
    return _exp
EOF

w backend/app/features/__init__.py <<'EOF'
# empty
EOF

w backend/app/features/detectors.py <<'EOF'
from ..clients.intellioptics_client import io_client

def ensure_basic_detector(name: str, query: str, confidence: float = 0.9):
    det = io_client().get_or_create_detector(name=name, query=query, confidence_threshold=confidence)
    return det
EOF

w backend/app/features/alerts.py <<'EOF'
from ..clients.intellioptics_client import exp_client
import os

BACKEND_WEBHOOK = os.getenv("BACKEND_WEBHOOK", "https://example.com/webhooks/intellioptics")

exp = exp_client()

def ensure_default_rule(detector_id: str, detector_name: str):
    action = exp.make_webhook_action(url=BACKEND_WEBHOOK, method="POST")
    condition = exp.make_condition(kind="CHANGED_TO", parameters={"label": "YES"})
    rule = exp.create_rule(detector=detector_id, rule_name=f"Alert {detector_name} YES", action=action, condition=condition, enabled=True)
    return rule
EOF

w backend/app/main.py <<'EOF'
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .schemas import SubmitQueryResponse, QueryStatusResponse, HumanLabelRequest
from .auth import require_auth
from .storage.blob import save_image_bytes
from .queues.servicebus import enqueue_image_query, enqueue_feedback
from .db import SessionLocal, Base, engine
from .models import ImageQueryRow
from .clients.intellioptics_client import io_client
from .migrations import migrate

Base.metadata.create_all(bind=engine)
migrate()

def create_app():
    app = FastAPI(title="IntelliOptics Backend", version="0.2.0")
    app.add_middleware(CORSMiddleware, allow_origins=[settings.allowed_origins] if settings.allowed_origins != "*" else ["*"], allow_methods=["*"], allow_headers=["*"])

    @app.post(f"{settings.api_base_path}/image-queries", response_model=SubmitQueryResponse, dependencies=[Depends(require_auth)])
    async def submit_image_query(detector_id: str, image: UploadFile = File(...)):
        content = await image.read()
        blob_url = await save_image_bytes(content, image.content_type or "image/jpeg")
        payload = {"detector_id": detector_id, "blob_url": blob_url}
        await enqueue_image_query(payload)
        return SubmitQueryResponse(image_query_id="queued", status="QUEUED")

    @app.get(f"{settings.api_base_path}/image-queries/{{image_query_id}}", response_model=QueryStatusResponse, dependencies=[Depends(require_auth)])
    async def get_status(image_query_id: str):
        with SessionLocal() as db:
            row = db.get(ImageQueryRow, image_query_id)
            if not row:
                iq = io_client().get_image_query(image_query_id)
                return QueryStatusResponse(
                    id=iq.id,
                    status="DONE" if iq.done_processing else "PROCESSING",
                    label=(iq.result.label if iq.result else None),
                    confidence=(iq.result.confidence if iq.result else None),
                    result_type=iq.result_type,
                    count=getattr(getattr(iq, "result", None), "count", None),
                    extra=None,
                )
            return QueryStatusResponse(id=row.id, status=row.status, label=row.label, confidence=row.confidence, result_type=row.result_type, count=row.count, extra=row.extra)

    @app.post(f"{settings.api_base_path}/image-queries/{{image_query_id}}/human-label", dependencies=[Depends(require_auth)])
    async def human_label(image_query_id: str, body: HumanLabelRequest):
        with SessionLocal() as db:
            row = db.get(ImageQueryRow, image_query_id)
            if not row:
                raise HTTPException(404, detail="image_query not found")
            row.human_label = body.label
            row.human_confidence = body.confidence
            row.human_notes = body.notes
            row.human_user = body.user
            if body.count is not None:
                row.count = body.count
            if body.extra is not None:
                row.extra = body.extra
            db.add(row); db.commit()
        await enqueue_feedback({
            "image_query_id": image_query_id,
            "label": body.label,
            "confidence": body.confidence,
            "count": body.count,
            "notes": body.notes,
            "user": body.user,
        })
        return {"ok": True}

    @app.post("/webhooks/intellioptics")
    async def webhook_ingest(payload: dict):
        return {"ok": True}

    return app
EOF

# --- worker
w worker-shim/Dockerfile <<'EOF'
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv && mkdir -p /app

COPY worker.py db.py models.py /app/

# deps
RUN python - <<'PY'
import os
pkgs = [
  'azure-identity','azure-servicebus','psycopg[binary]','sqlalchemy','pydantic','httpx','intellioptics-sdk-python'
]
os.system('pip install --no-cache-dir ' + ' '.join(pkgs))
PY

CMD ["python", "worker.py"]
EOF

w worker-shim/models.py <<'EOF'
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from sqlalchemy import String, Float, Boolean
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class ImageQueryRow(Base):
    __tablename__ = "image_queries"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    detector_id: Mapped[str] = mapped_column(String)
    blob_url: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="SUBMITTED")
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    result_type: Mapped[str | None] = mapped_column(String, nullable=True)
    count: Mapped[float | None] = mapped_column(Float, nullable=True)
    extra = mapped_column(JSONB, nullable=True)
    done_processing: Mapped[bool] = mapped_column(Boolean, default=False)
EOF

w worker-shim/db.py <<'EOF'
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

PG_DSN = os.getenv("POSTGRES_DSN") or (
    f"postgresql+psycopg://{os.getenv('PG_USER','postgres')}:{os.getenv('PG_PASSWORD','')}" \
    f"@{os.getenv('PG_HOST','localhost')}/{os.getenv('PG_DB','intellioptics')}?sslmode={os.getenv('PG_SSLMODE','require')}"
)
engine = create_engine(PG_DSN, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

with engine.connect() as c:
    c.execute(text("SELECT 1"))
EOF

w worker-shim/worker.py <<'EOF'
import json, os, time, logging, sys
from typing import Any, Dict
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from sqlalchemy.orm import Session
from models import ImageQueryRow, Base
from db import engine, SessionLocal
from intellioptics import IntelliOptics

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("worker-shim")

NS = os.getenv("AZ_SB_NAMESPACE")
CONN = os.getenv("SERVICE_BUS_CONN") or os.getenv("AZ_SB_CONN_STR")
QUEUE_IN = os.getenv("SB_QUEUE_LISTEN", "image-queries")
QUEUE_OUT = os.getenv("SB_QUEUE_SEND", "inference-results")

DEFAULT_CONFIDENCE = float(os.getenv("DEFAULT_CONFIDENCE", 0.9))
DEFAULT_TIMEOUT = float(os.getenv("DEFAULT_TIMEOUT", 30))

IO_TOKEN = os.getenv("INTELLIOPTICS_API_TOKEN") or os.getenv("INTELLOPTICS_API_TOKEN")
IO_ENDPOINT = os.getenv("INTELLIOPTICS_ENDPOINT") or os.getenv("INTELLOPTICS_API_BASE") or None

if not IO_TOKEN:
    log.error("INTELLIOPTICS_API_TOKEN is required")
    sys.exit(2)

cred = DefaultAzureCredential(exclude_shared_token_cache_credential=True)
if CONN:
    sb = ServiceBusClient.from_connection_string(CONN)
else:
    if not NS:
        log.error("Provide AZ_SB_NAMESPACE or SERVICE_BUS_CONN")
        sys.exit(2)
    sb = ServiceBusClient(fully_qualified_namespace=f"{NS}.servicebus.windows.net", credential=cred)

io = IntelliOptics(endpoint=IO_ENDPOINT, api_token=IO_TOKEN)
Base.metadata.create_all(bind=engine)


def _ensure_dict(msg_body: Any) -> Dict[str, Any]:
    if isinstance(msg_body, (bytes, bytearray)):
        msg_body = msg_body.decode("utf-8")
    if isinstance(msg_body, str):
        return json.loads(msg_body)
    if isinstance(msg_body, dict):
        return msg_body
    raise ValueError("Unsupported message body type")


def process_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if payload.get("kind") != "image-query":
        return {"skipped": True, "reason": f"unknown kind: {payload.get('kind')}"}

    det = payload["detector_id"]
    blob_url = payload["blob_url"]
    conf = float(payload.get("confidence_threshold", DEFAULT_CONFIDENCE))
    timeout = float(payload.get("timeout", DEFAULT_TIMEOUT))
    metadata = payload.get("metadata")

    iq = io.ask_async(detector=det, image=blob_url, metadata=metadata)
    iq = io.wait_for_confident_result(image_query=iq, confidence_threshold=conf, timeout_sec=timeout)

    r = getattr(iq, "result", None)
    count_val = None
    if r is not None:
        if getattr(iq, "result_type", None) == "COUNT":
            count_val = getattr(r, "count", None) or getattr(r, "value", None)
        try:
            extra = {k: v for k, v in r.__dict__.items() if k not in {"label", "confidence", "count", "value"}}
        except Exception:
            extra = None
    else:
        extra = None

    return {
        "image_query_id": iq.id,
        "status": "DONE" if getattr(iq, "done_processing", False) else "PROCESSING",
        "label": (r.label if r else None),
        "confidence": (r.confidence if r else None),
        "result_type": getattr(iq, "result_type", None),
        "count": count_val,
        "extra": extra,
        "detector_id": det,
        "blob_url": blob_url,
        "done_processing": bool(getattr(iq, "done_processing", False)),
        "metadata": metadata,
    }


def write_result_db(res: Dict[str, Any]):
    with SessionLocal() as db:  # type: Session
        row = db.get(ImageQueryRow, res["image_query_id"]) or ImageQueryRow(id=res["image_query_id"], detector_id=res["detector_id"], blob_url=res["blob_url"]) 
        row.status = res["status"]
        row.label = res.get("label")
        row.confidence = res.get("confidence")
        row.result_type = res.get("result_type")
        row.count = res.get("count")
        row.extra = res.get("extra")
        row.done_processing = res.get("done_processing", False)
        db.add(row); db.commit()


def send_result_queue(res: Dict[str, Any]):
    with sb.get_queue_sender(QUEUE_OUT) as sender:
        sender.send_messages(ServiceBusMessage(json.dumps({"kind": "result", **res})))


def run():
    log.info("Listening on '%s'", QUEUE_IN)
    with sb.get_queue_receiver(QUEUE_IN, max_wait_time=5) as receiver:
        for msg in receiver:
            try:
                payload = _ensure_dict(msg.body)
                res = process_payload(payload)
                if res.get("skipped"):
                    log.info("Skipping: %s", res["reason"]) 
                else:
                    try:
                        write_result_db(res)
                    except Exception as db_err:
                        log.warning("DB unavailable (%s). Sending to results queue.", db_err)
                        send_result_queue(res)
                receiver.complete_message(msg)
            except Exception as e:
                log.exception("Processing failed: %s", e)
                receiver.abandon_message(msg)
                time.sleep(1)

if __name__ == "__main__":
    run()
EOF

# --- GitHub Actions
w .github/workflows/worker-ci.yml <<'EOF'
name: worker-ci
on: { workflow_dispatch: {}, push: { branches: [ main ] } }
permissions: { id-token: write, contents: read }
jobs:
  build-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/docker-login@v2
        with:
          login-server: ${{ secrets.ACR_LOGIN_SERVER }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}
      - name: Build & push worker
        run: |
          docker build -t ${{ secrets.ACR_LOGIN_SERVER }}/${{ vars.IMAGE_NAME }}:${{ vars.IMAGE_TAG }} worker-shim
          docker push ${{ secrets.ACR_LOGIN_SERVER }}/${{ vars.IMAGE_NAME }}:${{ vars.IMAGE_TAG }}
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - name: Provision + Deploy worker (ACI)
        env:
          SERVICE_BUS_CONN: ${{ secrets.SERVICE_BUS_CONN }}
          AZ_SB_NAMESPACE: ${{ secrets.AZ_SB_NAMESPACE }}
          POSTGRES_DSN: ${{ secrets.POSTGRES_DSN }}
          INTELLIOPTICS_API_TOKEN: ${{ secrets.INTELLIOPTICS_API_TOKEN }}
          INTELLIOPTICS_ENDPOINT: ${{ vars.INTELLIOPTICS_ENDPOINT }}
          AZ_RESOURCE_GROUP: ${{ vars.AZ_RESOURCE_GROUP }}
          AZ_LOCATION: ${{ vars.AZ_LOCATION }}
          ACR_LOGIN_SERVER: ${{ secrets.ACR_LOGIN_SERVER }}
          IMAGE_NAME: ${{ vars.IMAGE_NAME }}
          IMAGE_TAG: ${{ vars.IMAGE_TAG }}
        run: bash deploy/aci-worker.sh
EOF

w .github/workflows/api-ci.yml <<'EOF'
name: api-ci
on: { workflow_dispatch: {}, push: { branches: [ main ] } }
permissions: { id-token: write, contents: read }
jobs:
  build-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/docker-login@v2
        with:
          login-server: ${{ secrets.ACR_LOGIN_SERVER }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}
      - name: Build & push API
        run: |
          docker build -t ${{ secrets.ACR_LOGIN_SERVER }}/intellioptics-api:latest backend
          docker push ${{ secrets.ACR_LOGIN_SERVER }}/intellioptics-api:latest
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - name: Provision + Deploy API (App Service)
        env:
          AZ_RESOURCE_GROUP: ${{ vars.AZ_RESOURCE_GROUP }}
          AZ_LOCATION: ${{ vars.AZ_LOCATION }}
          ACR_LOGIN_SERVER: ${{ secrets.ACR_LOGIN_SERVER }}
          AZ_SB_NAMESPACE: ${{ secrets.AZ_SB_NAMESPACE }}
          SERVICE_BUS_CONN: ${{ secrets.SERVICE_BUS_CONN }}
          AZ_BLOB_ACCOUNT: ${{ secrets.AZ_BLOB_ACCOUNT }}
          AZ_BLOB_CONTAINER: ${{ vars.AZ_BLOB_CONTAINER }}
          POSTGRES_DSN: ${{ secrets.POSTGRES_DSN }}
          PG_HOST: ${{ secrets.PG_HOST }}
          PG_DB: ${{ vars.PG_DB }}
          PG_USER: ${{ secrets.PG_USER }}
          PG_PASSWORD: ${{ secrets.PG_PASSWORD }}
          INTELLIOPTICS_API_TOKEN: ${{ secrets.INTELLIOPTICS_API_TOKEN }}
          INTELLIOPTICS_ENDPOINT: ${{ vars.INTELLIOPTICS_ENDPOINT }}
          API_PLAN: ${{ vars.API_PLAN }}
          WEBAPP: ${{ vars.WEBAPP }}
        run: bash deploy/appservice-api.sh
EOF

# --- summary
# create a zip next to the repo for easy download
ZIP_OUT="../intellioptics-oneclick.zip"
cd ..
if command -v zip >/dev/null 2>&1; then
  rm -f "$ZIP_OUT"
  zip -r "$ZIP_OUT" "intellioptics-oneclick" >/dev/null
elif command -v powershell >/dev/null 2>&1; then
  powershell -NoProfile -Command "Compress-Archive -Path 'intellioptics-oneclick' -DestinationPath 'intellioptics-oneclick.zip' -Force"
else
  tar -a -c -f "intellioptics-oneclick.zip" "intellioptics-oneclick" 2>/dev/null || tar -czf "intellioptics-oneclick.tar.gz" "intellioptics-oneclick"
fi

cat <<'EOF'

[ok] Repo scaffolded at ./intellioptics-oneclick
[ok] Zipped to ./intellioptics-oneclick.zip (or .tar.gz fallback)

Next steps:
1) If you haven't yet, set your Azure subscription:  
   az login && az account set --subscription "$AZ_SUBSCRIPTION_ID"
2) Unzip if you want to inspect:  
   unzip intellioptics-oneclick.zip
3) Deploy any time from inside the repo:  
   bash deploy/install.sh

EOF
