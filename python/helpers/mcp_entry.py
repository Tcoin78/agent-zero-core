"""
mcp_entry.py — Agent Zero MCP (Starlette + fastmcp ≥ 2.9.x)
────────────────────────────────────────────────────────────
POST /rfc   → ejecuta orden y responde JSON completo
POST /rfc/  → alias
GET  /events→ SSE (si helper lo ofrece)
GET  /health
GET  /metrics
"""

import os, inspect
from typing import Optional

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.middleware.cors import CORSMiddleware
from starlette_exporter import PrometheusMiddleware, handle_metrics

from python.helpers.mcp_server import mcp_server
from fastmcp.server import http as fhttp

# ──────────────────────────────────────────────────────────
# 1.  Seguridad opcional (Basic Auth)
# ──────────────────────────────────────────────────────────
USER = os.getenv("BASIC_AUTH_USERNAME")
PASSWD = os.getenv("BASIC_AUTH_PASSWORD")


def _auth(request: Request) -> Optional[JSONResponse]:
    """Devuelve JSON 401 si las credenciales son incorrectas."""
    if USER is None or PASSWD is None:        # Auth deshabilitada
        return None
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Basic "):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    import base64
    try:
        user_pass = base64.b64decode(auth[6:]).decode()
        username, password = user_pass.split(":", 1)
    except Exception:
        return JSONResponse({"detail": "Invalid header"}, status_code=401)
    if (username, password) != (USER, PASSWD):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return None


# ──────────────────────────────────────────────────────────
# 2.  Selección del helper fastmcp
# ──────────────────────────────────────────────────────────
if hasattr(fhttp, "create_blocking_app"):
    helper = fhttp.create_blocking_app
else:
    helper = fhttp.create_streamable_http_app        # tu versión

sig = inspect.signature(helper)
kwargs = {"server": mcp_server}
if "streamable_http_path" in sig.parameters:
    kwargs["streamable_http_path"] = "/rfc"

app: Starlette = helper(**kwargs)

# ──────────────────────────────────────────────────────────
# 3.  Alias /rfc/  + Health + Metrics
# ──────────────────────────────────────────────────────────
async def rfc_alias(request: Request):
    # auth
    err = _auth(request)
    if err:
        return err
    return JSONResponse({"status": "ack"})

app.add_route("/rfc/", rfc_alias, methods=["POST"])

async def health(_: Request):
    return JSONResponse({"status": "ok"})

app.add_route("/health", health, methods=["GET"])
app.add_route("/metrics", handle_metrics, methods=["GET"])

# ──────────────────────────────────────────────────────────
# 4.  Middleware global
# ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
app.add_middleware(
    PrometheusMiddleware, app_name="agent_zero_mcp", group_paths=True
)

# ──────────────────────────────────────────────────────────
# 5.  Arranque manual (debug)
# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mcp_entry:app", host="0.0.0.0", port=55080, reload=True)
