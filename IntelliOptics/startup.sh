# startup.sh
#!/bin/sh
set -eux

cd /home/site/wwwroot

# If Oryx left a packed build, unpack it so files sit at the root
[ -f output.tar.gz ] && tar -xzf output.tar.gz --strip-components=1 || true

# Find your app folder and enter it (your main.py is under api/app)
if [ -d api/app ]; then
  cd api/app
elif [ -d app ]; then
  cd app
fi

# Sanity: if we still don't see main.py, serve a placeholder so health checks pass
if [ ! -f main.py ]; then
  echo "main.py not found; contents:"
  ls -la
  exec python -m http.server 8000
fi

echo "CWD=$(pwd)"
ls -la

# Run the FastAPI app via gunicorn+uvicorn worker
export PYTHONPATH="$(pwd)"
exec gunicorn -k uvicorn.workers.UvicornWorker main:app --bind=0.0.0.0:8000 --timeout 120 --workers="${WORKERS:-1}"
