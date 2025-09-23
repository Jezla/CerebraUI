import logging
import uuid
import jwt
import base64
import hmac
import hashlib
import requests
import json
import os
import resend
import pyotp
import time

from datetime import datetime, timedelta
import pytz
from pytz import UTC
from typing import Optional, Union, List, Dict, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from redis import Redis


from open_webui.models.otp import Otp, otpTable, verifyTokenForm
from open_webui.models.users import Users
from open_webui.constants import ERROR_MESSAGES
from open_webui.env import (
    WEBUI_SECRET_KEY,
    TRUSTED_SIGNATURE_KEY,
    STATIC_DIR,
    SRC_LOG_LEVELS,
    RESEND_API_KEY,
)

from fastapi import BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext


logging.getLogger("passlib").setLevel(logging.ERROR)

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["OAUTH"])

SESSION_SECRET = WEBUI_SECRET_KEY
ALGORITHM = "HS256"

OTP_REDIS_TTL_SECONDS = 600


def _otp_redis_key(email: str) -> str:
    return f"open-webui:otp:{email.lower()}"


def _load_otp_from_redis(redis_client: Optional["Redis"], email: str) -> Optional[dict]:
    if not redis_client:
        return None

    raw_value = redis_client.get(_otp_redis_key(email))
    if not raw_value:
        return None

    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        log.warning("Failed to decode OTP payload from Redis for %s", email)
        redis_client.delete(_otp_redis_key(email))
        return None


def _store_otp_in_redis(redis_client: Optional["Redis"], email: str, payload: dict):
    if not redis_client:
        return

    redis_client.set(
        _otp_redis_key(email),
        json.dumps(payload),
        ex=OTP_REDIS_TTL_SECONDS,
    )


def _update_redis_record(
    redis_client: Optional["Redis"], email: str, payload: dict, ttl: Optional[int] = None
):
    if not redis_client:
        return

    ttl = ttl if ttl is not None and ttl >= 0 else OTP_REDIS_TTL_SECONDS
    redis_client.set(
        _otp_redis_key(email),
        json.dumps(payload),
        ex=ttl,
    )

##############
# Auth Utils
##############


def verify_signature(payload: str, signature: str) -> bool:
    """
    Verifies the HMAC signature of the received payload.
    """
    try:
        expected_signature = base64.b64encode(
            hmac.new(TRUSTED_SIGNATURE_KEY, payload.encode(), hashlib.sha256).digest()
        ).decode()

        # Compare securely to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)

    except Exception:
        return False


def override_static(path: str, content: str):
    # Ensure path is safe
    if "/" in path or ".." in path:
        log.error(f"Invalid path: {path}")
        return

    file_path = os.path.join(STATIC_DIR, path)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(base64.b64decode(content))  # Convert Base64 back to raw binary


def get_license_data(app, key):
    if key:
        try:
            res = requests.post(
                "https://api.openwebui.com/api/v1/license/",
                json={"key": key, "version": "1"},
                timeout=5,
            )

            if getattr(res, "ok", False):
                payload = getattr(res, "json", lambda: {})()
                for k, v in payload.items():
                    if k == "resources":
                        for p, c in v.items():
                            globals().get("override_static", lambda a, b: None)(p, c)
                    elif k == "count":
                        setattr(app.state, "USER_COUNT", v)
                    elif k == "name":
                        setattr(app.state, "WEBUI_NAME", v)
                    elif k == "metadata":
                        setattr(app.state, "LICENSE_METADATA", v)
                return True
            else:
                log.error(
                    f"License: retrieval issue: {getattr(res, 'text', 'unknown error')}"
                )
        except Exception as ex:
            log.exception(f"License: Uncaught Exception: {ex}")
    return False


bearer_security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return (
        pwd_context.verify(plain_password, hashed_password) if hashed_password else None
    )


def get_password_hash(password):
    return pwd_context.hash(password)


def create_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    payload = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
        payload.update({"exp": expire})

    encoded_jwt = jwt.encode(payload, SESSION_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        decoded = jwt.decode(token, SESSION_SECRET, algorithms=[ALGORITHM])
        return decoded
    except Exception:
        return None


def extract_token_from_auth_header(auth_header: str):
    return auth_header[len("Bearer ") :]


def create_api_key():
    key = str(uuid.uuid4()).replace("-", "")
    return f"sk-{key}"


def get_http_authorization_cred(auth_header: Optional[str]):
    if not auth_header:
        return None
    try:
        scheme, credentials = auth_header.split(" ")
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)
    except Exception:
        return None


def get_current_user(
    request: Request,
    background_tasks: BackgroundTasks,
    auth_token: HTTPAuthorizationCredentials = Depends(bearer_security),
):
    token = None

    if auth_token is not None:
        token = auth_token.credentials

    if token is None and "token" in request.cookies:
        token = request.cookies.get("token")

    if token is None:
        raise HTTPException(status_code=403, detail="Not authenticated")

    # auth by api key
    if token.startswith("sk-"):
        if not request.state.enable_api_key:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail=ERROR_MESSAGES.API_KEY_NOT_ALLOWED
            )

        if request.app.state.config.ENABLE_API_KEY_ENDPOINT_RESTRICTIONS:
            allowed_paths = [
                path.strip()
                for path in str(
                    request.app.state.config.API_KEY_ALLOWED_ENDPOINTS
                ).split(",")
            ]

            # Check if the request path matches any allowed endpoint.
            if not any(
                request.url.path == allowed
                or request.url.path.startswith(allowed + "/")
                for allowed in allowed_paths
            ):
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN, detail=ERROR_MESSAGES.API_KEY_NOT_ALLOWED
                )

        return get_current_user_by_api_key(token)

    # auth by jwt token
    try:
        data = decode_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    if data is not None and "id" in data:
        user = Users.get_user_by_id(data["id"])
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.INVALID_TOKEN,
            )
        else:
            # Refresh the user's last active timestamp asynchronously
            # to prevent blocking the request
            if background_tasks:
                background_tasks.add_task(Users.update_user_last_active_by_id, user.id)
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )


def get_current_user_by_api_key(api_key: str):
    user = Users.get_user_by_api_key(api_key)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.INVALID_TOKEN,
        )
    else:
        Users.update_user_last_active_by_id(user.id)

    return user


def get_verified_user(user=Depends(get_current_user)):
    if user.role not in {"user", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
    return user


def get_admin_user(user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
    return user


# Send email
def send_email(email: str, redis_client: Optional["Redis"] = None):
    try:
        otp_model = generate_otp(email=email, redis_client=redis_client)
        if otp_model is None:
            return None
    except Exception as e:
        print(e)
        raise HTTPException(500, detail=f"Failed to generate OTP: {e}")
    resend.api_key = RESEND_API_KEY
    params = {
        "from": "CerebraUI <no-reply@cerebraui.tech>",
        "to": [f"{email}"],
        "subject": "Your OTP for CerebraUI",
        "html": f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verification</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f9fafb;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #f9fafb;">
                <tr>
                    <td style="padding: 30px 10px;">
                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" 
                               style="max-width: 500px; margin: 0 auto; background: #ffffff; 
                                      border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                            <tr>
                                <td style="padding: 25px; text-align: center;">
                                    <h2 style="color: #333333; margin: 0 0 10px 0; font-size: 24px;">
                                        🔐 Verify Your Email
                                    </h2>
                                    <p style="color: #555555; font-size: 15px; line-height: 1.5; margin: 0 0 25px 0;">
                                        Please use the verification code below to continue with your request.
                                    </p>
                                    <div style="margin: 25px 0;">
                                        <span style="font-size: 32px; font-weight: bold; letter-spacing: 3px;
                                                     color: #2563eb; background-color: #eef2ff; padding: 12px 20px;
                                                     border-radius: 8px; display: inline-block;">
                                            {otp_model.otp}
                                        </span>
                                    </div>
                                    <div style="margin: 20px 0; padding: 20px 0;">
                                        <p style="color: #777777; font-size: 14px; line-height: 1.5; margin: 0;">
                                        This code will expire in <strong>10 minutes</strong>. 
                                        If you did not request this, you can safely ignore this email.
                                        </p>
                                    </div>
                                    <div style="border-top: 1px solid #eeeeee; padding-top: 20px; margin-top: 20px;">
                                        <p style="color: #aaaaaa; font-size: 14px; margin: 0; line-height: 1.4;">
                                        © 2025 CerebraUI. All rights reserved.
                                        </p>
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """,
    }
    try:
        resend.Emails.send(params)
    except Exception as e:
        print(e)
        raise HTTPException(500, detail=f"Failed to send email: {e}")
    return otp_model


# Generate OTP
def generate_otp(email: str, redis_client: Optional["Redis"] = None):
    normalized_email = email.lower()
    otp_secret = pyotp.random_base32()
    otp = pyotp.TOTP(otp_secret, digits=6, interval=600).now()
    otp_model = Otp(
        email=normalized_email,
        otp=hashlib.sha256(otp.encode()).hexdigest(),
        attempts=0,
        is_used=False,
    )
    token_data = {
        "email": otp_model.email,
        "otp": otp_model.otp,
    }
    token = create_token(token_data, expires_delta=timedelta(minutes=10))
    otp_model.token = hashlib.sha256(token.encode()).hexdigest()
    try:
        is_user_exist = Users.get_user_by_email(otp_model.email)
        if not is_user_exist:
            return None
    except Exception as e:
        print(e)
        raise HTTPException(500, detail=f"Failed to get user by email: {e}")
    # If an email has already tried to send an email, generate a new OTP and update the OTP and token in the table
    try:
        existing_attempts = 0
        if redis_client:
            existing_record = _load_otp_from_redis(redis_client, otp_model.email)
            if existing_record:
                existing_attempts = existing_record.get("attempts", 0)
                if existing_attempts >= 3:
                    raise HTTPException(
                        400,
                        detail="You have reached the maximum number of attempts. Please try again later.",
                    )

            payload = {
                "otp": otp_model.otp,
                "token": otp_model.token,
                "attempts": existing_attempts + 1,
                "is_used": False,
            }
            _store_otp_in_redis(redis_client, otp_model.email, payload)
        else:
            otp_exist = otpTable().get_otp_by_email(otp_model.email)
            if otp_exist:
                if otp_exist.attempts < 3:
                    otpTable().update_otp_by_email(
                        otp_model.email, otp_model.otp, otp_model.token
                    )
                    otpTable().increment_attempts(otp_model.email)
                    existing_attempts = otp_exist.attempts
                else:
                    raise HTTPException(
                        400,
                        detail="You have reached the maximum number of attempts. Please try again later.",
                    )
            else:
                otpTable().insert_new_otp(otp_model.email, otp_model.otp, otp_model.token)
                otpTable().increment_attempts(otp_model.email)
    # If the user has reached the maximum number of attempts, they will be limited and unable to request an email again
    except Exception as e:
        print(e)
        raise HTTPException(500, detail=f"Failed to save OTP to database: {e}")
    otp_model.attempts = existing_attempts + 1
    otp_model.otp = otp
    otp_model.token = token
    return otp_model


def verify_otp(email: str, otp: str, redis_client: Optional["Redis"] = None):
    otp_model = None
    normalized_email = email.lower() if email else email

    if normalized_email is not None and otp is not None:
        if redis_client:
            otp_model = _load_otp_from_redis(redis_client, normalized_email)
        else:
            otp_model = otpTable().get_otp_by_email(normalized_email)
    if otp_model is None:
        print("otp_model is None")
        return False
    attempts = (
        otp_model.get("attempts", 0)
        if isinstance(otp_model, dict)
        else getattr(otp_model, "attempts", 0)
    )
    if attempts >= 3:
        print("otp_model.attempts >= 3")
        return False
    is_used = (
        otp_model.get("is_used", False)
        if isinstance(otp_model, dict)
        else getattr(otp_model, "is_used", False)
    )
    if is_used:
        print("otp_model.is_used")
        return False
    stored_otp = (
        otp_model.get("otp") if isinstance(otp_model, dict) else otp_model.otp
    )
    if stored_otp == hashlib.sha256(otp.encode()).hexdigest():
        if redis_client and isinstance(otp_model, dict):
            otp_model["is_used"] = True
            key_ttl = redis_client.ttl(_otp_redis_key(normalized_email))
            # Only set TTL if it's a positive value; otherwise, preserve current state (no expiration)
            if key_ttl is not None and key_ttl > 0:
                _update_redis_record(redis_client, normalized_email, otp_model, ttl=key_ttl)
            else:
                _update_redis_record(redis_client, normalized_email, otp_model, ttl=None)
        else:
            otpTable().mark_as_used(normalized_email)

        token_data = {
            "email": normalized_email,
            "is_used": True,
        }
        token = create_token(token_data, expires_delta=timedelta(minutes=10))
        print("otp verification successful")
        return (True, token)

    print(f"{stored_otp == hashlib.sha256(otp.encode()).hexdigest()}")
    print("otp verification failed")
    return False


def verify_otp_token(data: verifyTokenForm):
    token = data.token
    email = data.email
    try:
        decoded_token = jwt.decode(token, SESSION_SECRET, algorithms=[ALGORITHM])
        if email != decoded_token.get("email"):
            raise HTTPException(400, detail="Email is Wrong. email does not match")
        else:
            print("token verification successful")
            return True
    except Exception as e:
        print(e)
        raise HTTPException(400, detail=f"Failed to verify OTP token: {e}")


def verify_reset_token(data: verifyTokenForm):
    token = data.token
    email = data.email
    try:
        decoded_token = jwt.decode(token, SESSION_SECRET, algorithms=[ALGORITHM])
        if email != decoded_token.get("email"):
            raise HTTPException(400, detail="Email is Wrong. email does not match")
        elif not decoded_token.get("is_used"):
            raise HTTPException(400, detail="Token is Wrong. token is used")
        else:
            print("token verification successful")
            return True
    except Exception as e:
        print(e)
        raise HTTPException(400, detail=f"Failed to verify OTP token: {e}")


def update_user_password_by_email(email: str, new_password: str):
    try:
        user = Users.get_user_by_email(email)
    except Exception as e:
        raise HTTPException(400, detail=f"Failed to get user by email: {e}")
    try:
        from open_webui.models.auths import Auths

        return Auths.update_user_password_by_id(user.id, new_password)
    except Exception as e:
        print(e)
        raise HTTPException(400, detail=f"Failed to update user password by id: {e}")


def check_email_attempts(email: str, redis_client: Optional["Redis"] = None):
    normalized_email = email.lower()

    if redis_client:
        otp_record = _load_otp_from_redis(redis_client, normalized_email)
        if otp_record:
            return otp_record.get("attempts", 0)
        return 0

    otp_record = otpTable().get_otp_by_email(normalized_email)
    return otp_record.attempts if otp_record else 0
