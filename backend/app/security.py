import hashlib
import secrets
from datetime import timedelta
from fastapi import Depends, HTTPException, Request
from pwdlib import PasswordHash
from sqlalchemy.orm import Session as DB
from .config import settings
from .db import get_db
from .models import Session, User, now

passwords = PasswordHash.recommended()
DUMMY_HASH = passwords.hash('constant-time-unknown-account')


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(request: Request, db: DB = Depends(get_db)):
    token = request.cookies.get('nexora_session', '')
    session = db.get(Session, token_hash(token))
    if not session or session.expires_at <= now():
        raise HTTPException(401, 'Please sign in')
    user = db.get(User, session.user_id)
    if not user or not user.active:
        raise HTTPException(401, 'Account unavailable')
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        if not secrets.compare_digest(request.headers.get('x-csrf-token', ''), session.csrf_token):
            raise HTTPException(403, 'Invalid security token; reload and try again')
    request.state.session = session
    return user


def require(user, *roles):
    if user.role not in roles:
        raise HTTPException(403, 'This action is not available for your role')


def create_session(db, user):
    raw = secrets.token_urlsafe(48)
    session = Session(token_hash=token_hash(raw), user_id=user.id, csrf_token=secrets.token_urlsafe(32),
                      expires_at=now() + timedelta(hours=settings().session_hours))
    db.add(session)
    return raw, session
