PORT="${PORT:-8080}"
uvicorn cerebraui.main:app --port $PORT --host 0.0.0.0 --forwarded-allow-ips --reload