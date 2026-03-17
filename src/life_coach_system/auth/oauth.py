"""Authlib OAuth client configuration for Google, Twitter, and Facebook."""

from authlib.integrations.starlette_client import OAuth

from life_coach_system.config import Settings

__all__ = ["create_oauth"]


def create_oauth(settings: Settings) -> OAuth:
    """Create and configure an Authlib OAuth instance with all providers."""
    oauth = OAuth()

    # Google — OpenID Connect
    if settings.google_client_id:
        oauth.register(
            name="google",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    # Twitter/X — OAuth 2.0 with PKCE
    if settings.twitter_client_id:
        oauth.register(
            name="twitter",
            client_id=settings.twitter_client_id,
            client_secret=settings.twitter_client_secret,
            authorize_url="https://twitter.com/i/oauth2/authorize",
            access_token_url="https://api.twitter.com/2/oauth2/token",
            api_base_url="https://api.twitter.com/2/",
            client_kwargs={"scope": "users.read tweet.read", "code_challenge_method": "S256"},
        )

    # Facebook — OAuth 2.0
    if settings.facebook_client_id:
        oauth.register(
            name="facebook",
            client_id=settings.facebook_client_id,
            client_secret=settings.facebook_client_secret,
            authorize_url="https://www.facebook.com/v18.0/dialog/oauth",
            access_token_url="https://graph.facebook.com/v18.0/oauth/access_token",
            api_base_url="https://graph.facebook.com/v18.0/",
            client_kwargs={"scope": "email public_profile"},
        )

    return oauth
