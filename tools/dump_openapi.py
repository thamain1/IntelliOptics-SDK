import sys, json, pathlib, traceback, os

def try_export(path: str) -> bool:
    print(f"[openapi] trying to import app from: {path}")
    sys.path.insert(0, path)
    try:
        from app.main import app  # expects an `app = FastAPI(...)` in app/main.py
    except Exception:
        print("[openapi] import failed:")
        traceback.print_exc()
        return False
    try:
        schema = app.openapi()
        pathlib.Path("spec").mkdir(parents=True, exist_ok=True)
        out = pathlib.Path("spec/openapi.json")
        out.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        print(f"[openapi] wrote {out.as_posix()}")
        return True
    except Exception:
        print("[openapi] app.openapi() failed:")
        traceback.print_exc()
        return False

# Hint for your app to avoid heavy startup in imports (you can use this in your code if needed)
os.environ.setdefault("INTELLIOPTICS_EXPORT_OPENAPI", "1")

# Try newest first, then fall back to the simpler trees
paths = [
    r".\api-service\Azure\intellioptics-oneclick\backend",
    r".\api-service\api",
    r".\api-service\IntelliOptics\api",
]

ok = False
for p in paths:
    if try_export(p):
        ok = True
        break

if not ok:
    sys.exit("[openapi] failed to export from all known paths")
