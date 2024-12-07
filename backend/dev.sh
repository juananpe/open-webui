PORT="${PORT:-8080}"
WEBUI_AUTH_TRUSTED_EMAIL_HEADER=X-User-Email WEBUI_AUTH_TRUSTED_NAME_HEADER=X-User-Name uvicorn open_webui.main:app --port $PORT --host 0.0.0.0 --forwarded-allow-ips '*' --reload
