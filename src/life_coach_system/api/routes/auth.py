"""
OAuth login/callback, auth status, and logout routes.
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from starlette.responses import RedirectResponse

from life_coach_system._logging import get_logger
from life_coach_system.api.dependencies import (
    get_current_user,
    get_oauth,
    get_storage,
    get_user_repository,
)
from life_coach_system.api.schemas import AuthStatusResponse, UserInfo
from life_coach_system.auth.jwt import create_access_token
from life_coach_system.auth.oauth import OAuth
from life_coach_system.auth.user_repository import UserRepository
from life_coach_system.config import settings
from life_coach_system.persistence.backend import PersistenceBackend

log = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

_COOKIE_NAME = "access_token"
_COOKIE_MAX_AGE = settings.jwt_expiry_minutes * 60


def _set_jwt_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
        path="/",
    )


@router.get("/login/{provider}")
async def login(provider: str, request: Request, oauth: OAuth = Depends(get_oauth)) -> Response:
    """Redirect the user to the OAuth provider's consent screen."""
    client = getattr(oauth, provider, None)
    if client is None:
        return RedirectResponse(url=f"/?error=unsupported_provider&provider={provider}")

    redirect_uri = f"{settings.oauth_redirect_base_url}/api/v1/auth/callback/{provider}"

    # Pass anonymous_id in state so we can migrate the session after login
    anonymous_id = request.query_params.get("anonymous_id", "")
    state_data = json.dumps({"anonymous_id": anonymous_id})
    request.session["oauth_state_data"] = state_data

    return await client.authorize_redirect(request, redirect_uri)


@router.get("/callback/{provider}")
async def callback(
    provider: str,
    request: Request,
    oauth: OAuth = Depends(get_oauth),
    user_repo: UserRepository = Depends(get_user_repository),
    storage: PersistenceBackend = Depends(get_storage),
) -> Response:
    """Handle the OAuth callback: find/create user, set JWT, redirect to app."""
    client = getattr(oauth, provider, None)
    if client is None:
        return RedirectResponse(url=f"/?error=unsupported_provider&provider={provider}")

    try:
        token = await client.authorize_access_token(request)
    except Exception:
        log.exception("oauth_callback_failed", provider=provider)
        return RedirectResponse(url="/?error=oauth_failed")

    # Extract user info from provider
    email, name, avatar_url, provider_id = await _extract_user_info(client, token, provider)

    # Find existing or create new user
    user = user_repo.find_by_oauth(provider=provider, provider_id=provider_id)
    if user is None:
        user = user_repo.create_user(
            email=email,
            name=name,
            avatar_url=avatar_url,
            provider=provider,
            provider_id=provider_id,
        )
        log.info("user_created", user_id=user["id"], provider=provider)
    else:
        log.info("user_login", user_id=user["id"], provider=provider)

    # Migrate anonymous session if applicable
    state_data = request.session.pop("oauth_state_data", "{}")
    parsed_state = json.loads(state_data)
    anonymous_id = parsed_state.get("anonymous_id", "")
    if anonymous_id:
        _migrate_anonymous_session(anonymous_id, user["id"], user_repo, storage)

    # Create JWT and set cookie
    jwt_token = create_access_token(
        user_id=user["id"],
        email=user.get("email"),
        name=user.get("name"),
        provider=provider,
    )
    response = RedirectResponse(url="/", status_code=302)
    _set_jwt_cookie(response, jwt_token)
    return response


@router.get("/me", response_model=AuthStatusResponse)
def auth_status(
    current_user: dict | None = Depends(get_current_user),
) -> AuthStatusResponse:
    """Return the current authentication status."""
    if current_user is None:
        return AuthStatusResponse(is_authenticated=False, user=None)

    return AuthStatusResponse(
        is_authenticated=True,
        user=UserInfo(
            id=current_user["sub"],
            email=current_user.get("email"),
            name=current_user.get("name"),
            provider=current_user.get("provider"),
        ),
    )


@router.post("/logout")
def logout() -> Response:
    """Clear the JWT cookie."""
    response = Response(content='{"ok": true}', media_type="application/json")
    response.delete_cookie(key=_COOKIE_NAME, path="/")
    return response


async def _extract_user_info(
    client: Any, token: dict, provider: str
) -> tuple[str | None, str | None, str | None, str]:
    """Extract email, name, avatar_url, and provider_id from OAuth token/userinfo."""
    if provider == "google":
        userinfo = token.get("userinfo", {})
        return (
            userinfo.get("email"),
            userinfo.get("name"),
            userinfo.get("picture"),
            userinfo["sub"],
        )

    if provider == "twitter":
        resp = await client.get(
            "users/me", token=token, params={"user.fields": "profile_image_url"}
        )
        data = resp.json().get("data", {})
        return (
            None,  # Twitter doesn't provide email in basic scope
            data.get("name"),
            data.get("profile_image_url"),
            data["id"],
        )

    if provider == "facebook":
        resp = await client.get("me", token=token, params={"fields": "id,name,email,picture"})
        data = resp.json()
        picture_url = data.get("picture", {}).get("data", {}).get("url")
        return (
            data.get("email"),
            data.get("name"),
            picture_url,
            data["id"],
        )

    return None, None, None, token.get("sub", "unknown")


def _migrate_anonymous_session(
    anonymous_id: str,
    user_id: str,
    user_repo: UserRepository,
    storage: PersistenceBackend,
) -> None:
    """Re-assign anonymous sessions to the authenticated user, then clean up."""
    # Find all sessions belonging to the anonymous user
    anonymous_sessions = storage.list_sessions(anonymous_id)
    for summary in anonymous_sessions:
        session_id = summary["session_id"]
        state = storage.load(session_id)
        if state is not None:
            state["user_id"] = user_id
            storage.save(session_id, state)
            log.info(
                "session_state_migrated",
                session_id=session_id,
                anonymous_id=anonymous_id,
                user_id=user_id,
            )

    user_repo.delete_anonymous_count(anonymous_id)
    log.info("anonymous_session_migrated", anonymous_id=anonymous_id, user_id=user_id)
