import sys, json, pathlib, os, traceback
def main():
    if len(sys.argv) < 2:
        print("[child] usage: export_openapi_child.py <app_base_path>")
        sys.exit(2)
    base = sys.argv[1]
    print(f"[child] base={base}")
    sys.path.insert(0, base)
    os.environ.setdefault("INTELLIOPTICS_EXPORT_OPENAPI", "1")  # hint to your app to avoid heavy init
    try:
        from app.main import app  # expects app/main.py with `app = FastAPI(...)`
    except Exception as e:
        print("[child] import failed")
        traceback.print_exc()
        sys.exit(3)
    try:
        schema = app.openapi()
        pathlib.Path("spec").mkdir(parents=True, exist_ok=True)
        out = pathlib.Path("spec/openapi.json")
        out.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        print(f"[child] wrote {out.as_posix()}")
        sys.exit(0)
    except Exception:
        print("[child] app.openapi() failed")
        traceback.print_exc()
        sys.exit(4)

if __name__ == "__main__":
    main()
