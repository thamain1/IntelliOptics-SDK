import sys, subprocess, pathlib, time

paths = [
    r".\api-service\api",                                      # simple tree (0.1.0)
    r".\api-service\IntelliOptics\api",                        # duplicate simple tree
    r".\api-service\Azure\intellioptics-oneclick\backend",     # newest (may be heavy)
]

child = r".\tools\_export_openapi_child.py"
timeout_seconds = 12

for p in paths:
    print(f"[driver] trying {p} with timeout={timeout_seconds}s")
    try:
        cp = subprocess.run(
            [sys.executable, child, p],
            check=False,
            timeout=timeout_seconds,
            text=True,
            capture_output=True,
        )
    except subprocess.TimeoutExpired:
        print(f"[driver] TIMEOUT on {p}, moving on…")
        continue

    print(cp.stdout, end="")
    if cp.stderr:
        print(cp.stderr, end="")

    if cp.returncode == 0:
        print("[driver] success")
        sys.exit(0)
    else:
        print(f"[driver] non-zero exit {cp.returncode} on {p}, trying next…")

print("[driver] failed to export from all paths")
sys.exit(1)
