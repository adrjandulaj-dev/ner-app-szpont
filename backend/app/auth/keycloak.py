from keycloak import KeycloakOpenID, KeycloakAdmin
from jose import jwt, JWTError
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
import logging

from ..config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


class KeycloakAuth:
    """Keycloak authentication handler"""

    def __init__(self):
        self.keycloak_openid = KeycloakOpenID(
            server_url=settings.keycloak_url,
            client_id=settings.keycloak_client_id,
            realm_name=settings.keycloak_realm,
            client_secret_key=settings.keycloak_client_secret
        )

        # Get public key for token validation
        try:
            self.public_key = (
                "-----BEGIN PUBLIC KEY-----\n"
                + self.keycloak_openid.public_key()
                + "\n-----END PUBLIC KEY-----"
            )
        except Exception as e:
            logger.warning(f"Could not fetch Keycloak public key: {e}")
            self.public_key = None

    def verify_token(self, token: str) -> Dict:
        """
        Verify and decode JWT token from Keycloak

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Verify token with Keycloak
            token_info = self.keycloak_openid.introspect(token)

            if not token_info.get("active"):
                raise HTTPException(
                    status_code=401,
                    detail="Token is not active"
                )

            # Decode token to get user info
            options = {
                "verify_signature": True,
                "verify_aud": False,
                "verify_exp": True
            }

            if self.public_key:
                decoded_token = jwt.decode(
                    token,
                    self.public_key,
                    algorithms=["RS256"],
                    options=options
                )
            else:
                # Fallback: just use introspection result
                decoded_token = token_info

            return decoded_token

        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(
                status_code=401,
                detail="Authentication failed"
            )

    def get_user_info(self, token: str) -> Dict:
        """
        Get user information from token

        Args:
            token: JWT token string

        Returns:
            User information dictionary
        """
        try:
            return self.keycloak_openid.userinfo(token)
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise HTTPException(
                status_code=401,
                detail="Could not retrieve user information"
            )


# Global instance
keycloak_auth = KeycloakAuth()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict:
    """
    Dependency to get current authenticated user

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        User information dictionary
    """
    token = credentials.credentials
    user_info = keycloak_auth.verify_token(token)
    return user_info


async def get_current_user_id(
    user: Dict = Depends(get_current_user)
) -> str:
    """
    Dependency to get current user ID

    Args:
        user: User information from get_current_user

    Returns:
        User ID string
    """
    user_id = user.get("sub") or user.get("preferred_username")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Could not extract user ID from token"
        )
    return user_id


# Optional: Admin client for user management
def get_keycloak_admin() -> KeycloakAdmin:
    """Get Keycloak admin client"""
    return KeycloakAdmin(
        server_url=settings.keycloak_url,
        username=settings.keycloak_admin_user,
        password=settings.keycloak_admin_password,
        realm_name=settings.keycloak_realm,
        verify=True
    )
