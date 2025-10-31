import importlib
import os
import sys
import types
from unittest.mock import Mock

import pytest


# Ensure the project root is available on the Python path so that
# modules such as ``backend.cerebraui`` can be imported during tests.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


try:  # pragma: no cover - only used when typer isn't installed
    import typer  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - executed in test env without typer
    typer_stub = types.ModuleType("typer")

    class _Exit(Exception):
        ...

    class _Typer:
        def __init__(self, *_, **__):
            pass

        def command(self, *_, **__):
            def decorator(func):
                return func

            return decorator

        def __call__(self, *_, **__):
            return None

    def _echo(*_, **__):
        return None

    def _option(*_, **__):
        return None

    typer_stub.Typer = _Typer
    typer_stub.Option = _option
    typer_stub.Exit = _Exit
    typer_stub.echo = _echo

    sys.modules["typer"] = typer_stub


try:  # pragma: no cover - only used when uvicorn isn't installed
    import uvicorn  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - executed in test env without uvicorn
    uvicorn_stub = types.ModuleType("uvicorn")

    def _run(*_, **__):
        return None

    uvicorn_stub.run = _run
    sys.modules["uvicorn"] = uvicorn_stub


def _ensure_module(name: str, module: types.ModuleType) -> None:
    if name not in sys.modules:
        sys.modules[name] = module


# Lightweight stubs for optional third-party dependencies used by the backend
# modules that the Redis unit tests import. These keep the tests isolated from
# external packages that are not installed in the execution environment.
if "jwt" not in sys.modules:
    import json

    jwt_stub = types.ModuleType("jwt")

    def _encode(payload, key, algorithm=None):  # pragma: no cover - simple stub
        return json.dumps({"payload": payload, "key": key, "alg": algorithm})

    def _decode(token, key, algorithms=None):  # pragma: no cover - simple stub
        data = json.loads(token)
        if data.get("key") != key:
            raise ValueError("Invalid signature")
        return data.get("payload", {})

    jwt_stub.encode = _encode
    jwt_stub.decode = _decode
    _ensure_module("jwt", jwt_stub)


if "requests" not in sys.modules:
    requests_stub = types.ModuleType("requests")

    class _Response:  # pragma: no cover - simple stub
        def __init__(self, ok=False, text="", json_data=None):
            self.ok = ok
            self.text = text
            self._json = json_data or {}

        def json(self):
            return self._json

    def _post(*_, **__):  # pragma: no cover - simple stub
        return _Response()

    requests_stub.post = _post
    _ensure_module("requests", requests_stub)


if "resend" not in sys.modules:
    resend_stub = types.ModuleType("resend")
    resend_stub.api_key = ""

    class _Emails:  # pragma: no cover - simple stub
        @staticmethod
        def send(*_, **__):
            return None

    resend_stub.Emails = _Emails
    _ensure_module("resend", resend_stub)


if "pyotp" not in sys.modules:
    pyotp_stub = types.ModuleType("pyotp")

    class _TOTP:  # pragma: no cover - simple stub
        def __init__(self, secret, digits=6, interval=30):
            self.secret = secret
            self.digits = digits
            self.interval = interval

        def now(self):
            return "0" * self.digits

    pyotp_stub.random_base32 = lambda: "A" * 16
    pyotp_stub.TOTP = _TOTP
    _ensure_module("pyotp", pyotp_stub)


if "pytz" not in sys.modules:
    pytz_stub = types.ModuleType("pytz")

    class _UTC:  # pragma: no cover - simple stub
        def __repr__(self):
            return "UTC"

    pytz_stub.UTC = _UTC()
    _ensure_module("pytz", pytz_stub)


if "sympy" not in sys.modules:
    sympy_stub = types.ModuleType("sympy")
    sympy_stub.false = False
    _ensure_module("sympy", sympy_stub)


if "passlib" not in sys.modules:
    passlib_stub = types.ModuleType("passlib")
    passlib_context_stub = types.ModuleType("passlib.context")

    class _CryptContext:  # pragma: no cover - simple stub
        def __init__(self, *_, **__):
            pass

        def verify(self, plain_password, hashed_password):
            return plain_password == hashed_password

        def hash(self, password):
            return f"hashed-{password}"

    passlib_context_stub.CryptContext = _CryptContext
    passlib_stub.context = passlib_context_stub
    _ensure_module("passlib", passlib_stub)
    _ensure_module("passlib.context", passlib_context_stub)


if "fastapi" not in sys.modules:
    fastapi_stub = types.ModuleType("fastapi")

    class HTTPException(Exception):  # pragma: no cover - simple stub
        def __init__(self, status_code: int, detail=None):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    class BackgroundTasks:  # pragma: no cover - simple stub
        ...

    def Depends(callable_obj):  # pragma: no cover - simple stub
        return callable_obj

    class APIRouter:  # pragma: no cover - simple stub
        def __init__(self):
            self.routes = []

        def _decorator(self, *_, **__):
            def wrapper(func):
                return func

            return wrapper

        get = post = delete = put = patch = _decorator

    class Request:  # pragma: no cover - simple stub
        def __init__(self):
            self.app = types.SimpleNamespace(state=types.SimpleNamespace(config=None))

    class Response:  # pragma: no cover - simple stub
        ...

    status = types.SimpleNamespace(
        HTTP_400_BAD_REQUEST=400,
        HTTP_401_UNAUTHORIZED=401,
        HTTP_404_NOT_FOUND=404,
    )

    fastapi_stub.BackgroundTasks = BackgroundTasks
    fastapi_stub.APIRouter = APIRouter
    fastapi_stub.Depends = Depends
    fastapi_stub.HTTPException = HTTPException
    fastapi_stub.Request = Request
    fastapi_stub.Response = Response
    fastapi_stub.status = status
    _ensure_module("fastapi", fastapi_stub)


if "fastapi.security" not in sys.modules:
    fastapi_security_stub = types.ModuleType("fastapi.security")

    class HTTPAuthorizationCredentials:  # pragma: no cover - simple stub
        def __init__(self, scheme="", credentials=""):
            self.scheme = scheme
            self.credentials = credentials

    class HTTPBearer:  # pragma: no cover - simple stub
        def __init__(self, auto_error: bool = True):
            self.auto_error = auto_error

        def __call__(self, *_, **__):
            return HTTPAuthorizationCredentials()

    fastapi_security_stub.HTTPAuthorizationCredentials = HTTPAuthorizationCredentials
    fastapi_security_stub.HTTPBearer = HTTPBearer
    _ensure_module("fastapi.security", fastapi_security_stub)


if "pydantic" not in sys.modules:
    pydantic_stub = types.ModuleType("pydantic")

    class BaseModel:  # pragma: no cover - simple stub
        def __init__(self, **data):
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self):
            return self.__dict__.copy()

    pydantic_stub.BaseModel = BaseModel
    _ensure_module("pydantic", pydantic_stub)


# Minimal "cerebraui" package structure with just the pieces required for the
# Redis unit tests. Each submodule is defined only if it does not already exist
# so that a real installation takes precedence.
if "cerebraui" not in sys.modules:
    cerebraui_stub = types.ModuleType("cerebraui")
    cerebraui_stub.__path__ = []  # type: ignore[attr-defined]
    _ensure_module("cerebraui", cerebraui_stub)

if "cerebraui.constants" not in sys.modules:
    constants_stub = types.ModuleType("cerebraui.constants")
    constants_stub.ERROR_MESSAGES = types.SimpleNamespace(
        ACCESS_PROHIBITED="Access prohibited",
        DEFAULT=lambda: "An error occurred",
    )
    _ensure_module("cerebraui.constants", constants_stub)


if "cerebraui.env" not in sys.modules:
    env_stub = types.ModuleType("cerebraui.env")
    env_stub.WEBUI_SECRET_KEY = "test-secret"
    env_stub.TRUSTED_SIGNATURE_KEY = b"trusted-key"
    env_stub.STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
    env_stub.SRC_LOG_LEVELS = {"OAUTH": "INFO", "MODELS": "INFO"}
    env_stub.RESEND_API_KEY = "test-key"
    env_stub.UVICORN_WORKERS = 1
    _ensure_module("cerebraui.env", env_stub)


if "cerebraui.models" not in sys.modules:
    models_stub = types.ModuleType("cerebraui.models")
    _ensure_module("cerebraui.models", models_stub)


if "cerebraui.models.otp" not in sys.modules:
    otp_stub = types.ModuleType("cerebraui.models.otp")

    class Otp:  # pragma: no cover - simple stub
        def __init__(self, email: str, otp: str, attempts: int, is_used: bool, token: str | None = None):
            self.email = email
            self.otp = otp
            self.attempts = attempts
            self.is_used = is_used
            self.token = token

    class verifyTokenForm:  # pragma: no cover - simple stub
        def __init__(self, email: str, token: str):
            self.email = email
            self.token = token

    class _OtpTable:  # pragma: no cover - simple stub
        _store: dict[str, dict] = {}

        def insert_new_otp(self, email: str, otp: str, token: str):
            record = {"email": email, "otp": otp, "attempts": 0, "is_used": False, "token": token}
            self._store[email] = record.copy()
            return types.SimpleNamespace(**record)

        def delete_otp_by_email(self, email: str) -> bool:
            return self._store.pop(email, None) is not None

        def get_otp_by_email(self, email: str):
            record = self._store.get(email)
            return types.SimpleNamespace(**record) if record else None

        def update_otp_by_email(self, email: str, otp: str, token: str) -> bool:
            if email in self._store:
                self._store[email].update({"otp": otp, "token": token})
                return True
            return False

        def increment_attempts(self, email: str) -> bool:
            if email in self._store:
                self._store[email]["attempts"] += 1
                return True
            return False

        def mark_as_used(self, email: str) -> bool:
            if email in self._store:
                self._store[email]["is_used"] = True
                return True
            return False

    otp_stub.Otp = Otp
    otp_stub.otpTable = _OtpTable
    otp_stub.verifyTokenForm = verifyTokenForm
    _ensure_module("cerebraui.models.otp", otp_stub)


if "cerebraui.models.users" not in sys.modules:
    users_stub = types.ModuleType("cerebraui.models.users")

    class Users:  # pragma: no cover - simple stub
        @staticmethod
        def get_user_by_email(_email: str):
            return None

        @staticmethod
        def update_user_is_email_verified_by_id(_user_id, _value: bool):
            return None

    users_stub.Users = Users
    _ensure_module("cerebraui.models.users", users_stub)


if "cerebraui.socket" not in sys.modules:
    socket_stub = types.ModuleType("cerebraui.socket")
    socket_stub.__path__ = []  # type: ignore[attr-defined]
    _ensure_module("cerebraui.socket", socket_stub)


if "cerebraui.socket.main" not in sys.modules:
    socket_main_stub = types.ModuleType("cerebraui.socket.main")

    def get_event_emitter():  # pragma: no cover - simple stub
        return None

    socket_main_stub.get_event_emitter = get_event_emitter
    _ensure_module("cerebraui.socket.main", socket_main_stub)


if "cerebraui.models.tags" not in sys.modules:
    tags_stub = types.ModuleType("cerebraui.models.tags")

    class TagModel:  # pragma: no cover - simple stub
        def __init__(self, **data):
            self.__dict__.update(data)

        def model_dump(self):
            return self.__dict__.copy()

    class Tags:  # pragma: no cover - simple stub
        @staticmethod
        def get_tag_by_name_and_user_id(_name, _user_id):
            return None

        @staticmethod
        def insert_new_tag(_name, _user_id):
            return None

        @staticmethod
        def delete_tag_by_name_and_user_id(_name, _user_id):
            return None

    tags_stub.TagModel = TagModel
    tags_stub.Tags = Tags
    _ensure_module("cerebraui.models.tags", tags_stub)


if "cerebraui.models.folders" not in sys.modules:
    folders_stub = types.ModuleType("cerebraui.models.folders")

    class Folders:  # pragma: no cover - simple stub
        @staticmethod
        def get_children_folders_by_id_and_user_id(_folder_id, _user_id):
            return []

    folders_stub.Folders = Folders
    _ensure_module("cerebraui.models.folders", folders_stub)


if "cerebraui.models.chats" not in sys.modules:
    chats_stub = types.ModuleType("cerebraui.models.chats")

    class _BaseChatModel:
        def __init__(self, **data):
            self.__dict__.update(data)

        def model_dump(self):
            return self.__dict__.copy()

    class ChatForm(_BaseChatModel):
        ...

    class ChatImportForm(_BaseChatModel):
        ...

    class ChatResponse(_BaseChatModel):
        ...

    class ChatTitleIdResponse(_BaseChatModel):
        ...

    class Chats:  # pragma: no cover - simple stub
        @staticmethod
        def get_chat_title_id_list_by_user_id(*_, **__):
            return []

        @staticmethod
        def delete_chats_by_user_id(*_, **__):
            return True

        @staticmethod
        def get_chat_list_by_user_id(*_, **__):
            return []

        @staticmethod
        def insert_new_chat(*_, **__):
            return ChatResponse(id="chat", title="Chat")

        @staticmethod
        def import_chat(*_, **__):
            return ChatResponse(id="chat", title="Chat", meta={})

        @staticmethod
        def get_chats_by_user_id_and_search_text(*_, **__):
            return []

        @staticmethod
        def get_chats_by_folder_ids_and_user_id(*_, **__):
            return []

    chats_stub.ChatForm = ChatForm
    chats_stub.ChatImportForm = ChatImportForm
    chats_stub.ChatResponse = ChatResponse
    chats_stub.ChatTitleIdResponse = ChatTitleIdResponse
    chats_stub.Chats = Chats
    _ensure_module("cerebraui.models.chats", chats_stub)


if "cerebraui.utils" not in sys.modules:
    utils_stub = types.ModuleType("cerebraui.utils")
    utils_stub.__path__ = []  # type: ignore[attr-defined]
    _ensure_module("cerebraui.utils", utils_stub)


if "cerebraui.utils.access_control" not in sys.modules:
    access_control_stub = types.ModuleType("cerebraui.utils.access_control")

    def has_permission(*_, **__):  # pragma: no cover - simple stub
        return True

    access_control_stub.has_permission = has_permission
    _ensure_module("cerebraui.utils.access_control", access_control_stub)


if "cerebraui.config" not in sys.modules:
    config_stub = types.ModuleType("cerebraui.config")
    config_stub.ENABLE_ADMIN_CHAT_ACCESS = True
    config_stub.ENABLE_ADMIN_EXPORT = True
    _ensure_module("cerebraui.config", config_stub)


# Import the real backend modules after the supporting stubs are prepared so
# that the unit tests exercise the production Redis helpers.
backend_auth_module = importlib.import_module("backend.cerebraui.utils.auth")
sys.modules.setdefault("cerebraui.utils.auth", backend_auth_module)


@pytest.fixture
def mock_redis_client():
    """Fixture providing a mock Redis client"""
    return Mock()


@pytest.fixture
def sample_email():
    """Sample email for testing"""
    return "test@example.com"


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    return "user123"


@pytest.fixture
def sample_chat_id():
    """Sample chat ID for testing"""
    return "chat456"
