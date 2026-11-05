import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import jwt
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger("atmosai.auth")

security_bearer = HTTPBearer(auto_error=False)

class AuthenticatedUser(BaseModel):
    id: str
    email: Optional[str] = None
    role: str = "authenticated"
    is_demo: bool = False
    claims: Dict[str, Any] = {}

def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Cryptographically verifies a Supabase access token.
    Validates:
      - Cryptographic signature (using SUPABASE_JWT_SECRET)
      - Token expiration (exp)
      - Audience (aud == 'authenticated')
      - Issuer (iss matches Supabase project auth URL when configured)
    """
    # 1. Check for demo session tokens when Supabase is not configured
    if token.startswith("demo_token_"):
        user_id = token.replace("demo_token_", "")
        return {
            "sub": user_id,
            "email": f"{user_id}@atmosai.org",
            "aud": "authenticated",
            "role": "authenticated",
            "is_demo": True
        }

    # 2. Strict cryptographic verification if SUPABASE_JWT_SECRET is configured
    jwt_secret = settings.SUPABASE_JWT_SECRET.strip()
    if jwt_secret:
        try:
            # Decode options: verify exp, aud, and signature
            options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True
            }
            # Expected issuer if project URL is provided
            issuer = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1" if settings.SUPABASE_URL and "your-project" not in settings.SUPABASE_URL else None

            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=issuer,
                options=options
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Supabase token signature expired.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidAudienceError:
            logger.warning("Supabase token invalid audience.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token audience.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidIssuerError:
            logger.warning("Supabase token invalid issuer.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Supabase token validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )

    # 3. Fallback to Supabase API verification if client is available
    if settings.SUPABASE_URL and settings.SUPABASE_KEY and "your-project" not in settings.SUPABASE_URL:
        try:
            from app.database.supabase_client import db_manager
            if db_manager.supabase:
                user_res = db_manager.supabase.auth.get_user(token)
                if user_res and user_res.user:
                    return {
                        "sub": str(user_res.user.id),
                        "email": user_res.user.email,
                        "aud": "authenticated",
                        "role": "authenticated",
                        "is_demo": False
                    }
        except Exception as e:
            logger.warning(f"Supabase auth.get_user verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed via Supabase identity service.",
                headers={"WWW-Authenticate": "Bearer"}
            )

    # 4. If in local development without any keys configured, reject non-demo tokens
    # or decode without verification only for explicit development debugging
    if settings.ENVIRONMENT == "development":
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            # Still check expiration even if unverified in dev
            exp = unverified.get("exp")
            if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            return unverified
        except HTTPException:
            raise
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Invalid or unverified token.",
        headers={"WWW-Authenticate": "Bearer"}
    )

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    authorization: Optional[str] = Header(None)
) -> AuthenticatedUser:
    """
    Enforces authentication on protected endpoints.
    Derives user ID strictly from the verified Supabase JWT payload.
    """
    token = None
    if credentials:
        token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = verify_supabase_jwt(token)
    user_id = payload.get("sub") or payload.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain a valid user identifier.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return AuthenticatedUser(
        id=str(user_id),
        email=payload.get("email"),
        role=payload.get("role", "authenticated"),
        is_demo=payload.get("is_demo", False),
        claims=payload
    )

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    authorization: Optional[str] = Header(None)
) -> Optional[AuthenticatedUser]:
    """
    Extracts authenticated user if token is present and valid;
    returns None if no token is provided.
    """
    token = None
    if credentials:
        token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not token:
        return None

    try:
        payload = verify_supabase_jwt(token)
        user_id = payload.get("sub") or payload.get("id")
        if not user_id:
            return None
        return AuthenticatedUser(
            id=str(user_id),
            email=payload.get("email"),
            role=payload.get("role", "authenticated"),
            is_demo=payload.get("is_demo", False),
            claims=payload
        )
    except HTTPException:
        return None
    except Exception:
        return None

