import jwt
import os
import json
from fastapi import HTTPException, Request
from typing import Dict
from .config import settings
import logging

logger = logging.getLogger(__name__)


def verify_jwt_token(request: Request) -> Dict:
    """
    Verify JWT token using configured public key. In development, when `DEV_AUTH_BYPASS=true`
    and no `JWT_PUBLIC_KEY` is configured, allow a developer bypass via the `X-Dev-User`
    request header containing a JSON object with user claims.
    """
    auth_header = request.headers.get('authorization') or ''
    token = ''
    if auth_header.lower().startswith('bearer '):
        token = auth_header.split(' ', 1)[1].strip()

    # Production path: verify JWT with configured public key
    if settings.JWT_PUBLIC_KEY:
        try:
            if not token:
                raise jwt.PyJWTError('Missing token')
            payload = jwt.decode(token, settings.JWT_PUBLIC_KEY, algorithms=[settings.JWT_ALGORITHM], options={"verify_aud": False})
        except jwt.PyJWTError as e:
            raise HTTPException(status_code=401, detail='Invalid auth token') from e
        user_claims = {
            'sub': payload.get('sub'),
            'department': payload.get('department'),
            'employment_status': payload.get('employment_status'),
            'location': payload.get('location'),
            'role_level': payload.get('role_level'),
        }
        return user_claims

    # Development bypass: allow simple testing without JWT public key
    if getattr(settings, 'DEV_AUTH_BYPASS', False):
        logger.debug('DEV_AUTH_BYPASS enabled')
        logger.debug('Authorization header: %s', auth_header)
        # Prefer explicit X-Dev-User header, otherwise use configured DEV_USER_JSON from settings
        dev_header = request.headers.get('x-dev-user')
        if not dev_header and getattr(settings, 'DEV_USER_JSON', None):
            dev_header = settings.DEV_USER_JSON

        if dev_header:
            logger.debug('Using dev header for user: %s', dev_header)
            try:
                data = json.loads(dev_header)
            except Exception:
                logger.exception('Failed to parse dev header JSON')
                data = {}
        else:
            logger.debug('No dev header provided; using defaults')
            data = {}
        return {
            'sub': data.get('sub', 'dev-user'),
            'department': data.get('department', 'HR'),
            'employment_status': data.get('employment_status', 'active'),
            'location': data.get('location', 'US'),
            'role_level': data.get('role_level', 'L2'),
        }

    # If we reach here, auth is not configured
    raise HTTPException(status_code=401, detail='No JWT public key configured')
