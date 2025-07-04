import os
import secrets
import time
import socket
import struct
import threading
import signal
from functools import wraps
from flask import Flask, request, Response, session
from flask_basicauth import BasicAuth

import initialize
from python.helpers import errors, files, git, mcp_server
from python.helpers.files import get_abs_path
from python.helpers import runtime, dotenv, process
from python.helpers.extract_tools import load_classes_from_folder
from python.helpers.api import ApiHandler
from python.helpers.print_style import PrintStyle

# Set timezone to UTC
os.environ["TZ"] = "UTC"
time.tzset()

webapp = Flask("app", static_folder=get_abs_path("./webui"), static_url_path="/")
webapp.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
webapp.config.update(
    JSON_SORT_KEYS=False,
    SESSION_COOKIE_SAMESITE="Strict",
)

lock = threading.Lock()
basic_auth = BasicAuth(webapp)


def is_loopback_address(address):
    loopback_checker = {
        socket.AF_INET: lambda x: struct.unpack("!I", socket.inet_aton(x))[0] >> (32 - 8) == 127,
        socket.AF_INET6: lambda x: x == "::1",
    }
    try:
        socket.inet_pton(socket.AF_INET, address)
        return loopback_checker[socket.AF_INET](address)
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, address)
            return loopback_checker[socket.AF_INET6](address)
        except socket.error:
            pass

    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            r = socket.getaddrinfo(address, None, family, socket.SOCK_STREAM)
        except socket.gaierror:
            return False
        for family, _, _, _, sockaddr in r:
            if not loopback_checker[family](sockaddr[0]):
                return False
    return True


def requires_api_key(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        valid_api_key = dotenv.get_dotenv_value("API_KEY")
        if api_key := request.headers.get("X-API-KEY"):
            if api_key != valid_api_key:
                return Response("API key required", 401)
        elif request.json and request.json.get("api_key"):
            api_key = request.json.get("api_key")
            if api_key != valid_api_key:
                return Response("API key required", 401)
        else:
            return Response("API key required", 401)
        return await f(*args, **kwargs)
    return decorated


def requires_loopback(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        if not is_loopback_address(request.remote_addr):
            return Response("Access denied.", 403)
        return await f(*args, **kwargs)
    return decorated


def requires_auth(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        user = dotenv.get_dotenv_value("AUTH_LOGIN")
        password = dotenv.get_dotenv_value("AUTH_PASSWORD")
        if user and password:
            auth = request.authorization
            if not auth or not (auth.username == user and auth.password == password):
                return Response(
                    "Could not verify your access level.\n"
                    "You have to login with proper credentials",
                    401,
                    {"WWW-Authenticate": 'Basic realm="Login Required"'},
                )
        return await f(*args, **kwargs)
    return decorated


def csrf_protect(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        token = session.get("csrf_token")
        header = request.headers.get("X-CSRF-Token")
        if not token or not header or token != header:
            return Response("CSRF token missing or invalid", 403)
        return await f(*args, **kwargs)
    return decorated


@webapp.route("/", methods=["GET"])
@requires_auth
async def serve_index():
    try:
        gitinfo = git.get_git_info()
    except Exception:
        gitinfo = {"version": "unknown", "commit_time": "unknown"}
    return files.read_file(
        "./webui/index.html",
        version_no=gitinfo["version"],
        version_time=gitinfo["commit_time"],
    )


def run():
    PrintStyle().print("Initializing framework...")

    from werkzeug.serving import WSGIRequestHandler, make_server
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from a2wsgi import ASGIMiddleware

    class NoRequestLoggingWSGIRequestHandler(WSGIRequestHandler):
        def log_request(self, code="-", size="-"):
            pass

    port = int(os.getenv("WEB_UI_PORT", "5000"))
    host = runtime.get_arg("host") or dotenv.get_dotenv_value("WEB_UI_HOST") or "localhost"

    def register_api_handler(app, handler: type[ApiHandler]):
        name = handler.__module__.split(".")[-1]
        instance = handler(app, lock)

        async def handler_wrap():
            return await instance.handle_request(request=request)

        if handler.requires_loopback():
            handler_wrap = requires_loopback(handler_wrap)
        if handler.requires_auth():
            handler_wrap = requires_auth(handler_wrap)
        if handler.requires_api_key():
            handler_wrap = requires_api_key(handler_wrap)
        if handler.requires_csrf():
            handler_wrap = csrf_protect(handler_wrap)

        app.add_url_rule(
            f"/{name}", f"/{name}", handler_wrap, methods=handler.get_methods()
        )

    handlers = load_classes_from_folder("python/api", "*.py", ApiHandler)
    for handler in handlers:
        register_api_handler(webapp, handler)

    app = DispatcherMiddleware(
        webapp,
        {
            "/mcp": ASGIMiddleware(app=mcp_server.DynamicMcpProxy.get_instance()),  # type: ignore
        },
    )
    PrintStyle().debug("Registered middleware for MCP and MCP token")
    PrintStyle().debug(f"Starting server at {host}:{port}...")

    server = make_server(
        host=host,
        port=port,
        app=app,
        request_handler=NoRequestLoggingWSGIRequestHandler,
        threaded=True,
    )

    process.set_server(server)
    server.log_startup()

    # Start initialization in background
    threading.Thread(target=init_a0, daemon=True).start()

    server.serve_forever()


def init_a0():
    try:
        init_chats = initialize.initialize_chats()
        initialize.initialize_mcp()

        # Start job loop only if RFC is configured
        rfc_password = dotenv.get_dotenv_value("RFC_PASSWORD")
        if rfc_password:
            initialize.initialize_job_loop()
        else:
           print(f"[🔐] RFC_PASSWORD = {dotenv.get_dotenv_value('RFC_PASSWORD')}")
        
        init_chats.result_sync()

    except Exception as e:
        PrintStyle().error(f"[❌] Error initializing A0: {e}")


if __name__ == "__main__":
    runtime.initialize()
    dotenv.load_dotenv()
    run()
