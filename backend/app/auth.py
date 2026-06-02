import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Dict
from .config import settings

security = HTTPBearer()


def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict:
    token = credentials.credentials
    try:
        if settings.JWT_PUBLIC_KEY:
            payload = jwt.decode(token, settings.JWT_PUBLIC_KEY, algorithms=[settings.JWT_ALGORITHM], options={"verify_aud": False})
        else:
            # No public key configured; reject
            raise Exception('No JWT public key configured')
        # Basic required claims
        user_claims = {
            'sub': payload.get('sub'),
            'department': payload.get('department'),
            'employment_status': payload.get('employment_status'),
            'location': payload.get('location'),
            'role_level': payload.get('role_level'),
        }
        return user_claims
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail='Invalid auth token') from e
