import logging
import time
from collections import defaultdict, deque
from threading import Lock
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from .db import engine
from .config import settings
from .routes import router
from .learning import router as learning_router
from .arena import router as arena_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('nexora')
app = FastAPI(title='Nexora AI', version='0.1.0', docs_url='/api/docs' if settings().environment != 'production' else None)
app.include_router(router)
app.include_router(learning_router)
app.include_router(arena_router)
buckets = defaultdict(deque)
bucket_lock = Lock()


@app.middleware('http')
async def protection(request: Request, call_next):
    started = time.monotonic()
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        origin = request.headers.get('origin')
        if origin and origin != settings().frontend_origin:
            return JSONResponse({'detail': 'Origin not allowed'}, 403)
        if int(request.headers.get('content-length', '0')) > 11 * 1024 * 1024:
            return JSONResponse({'detail': 'Request too large'}, 413)
    # In-process limiter for one replica. Do not trust user-controlled forwarded headers.
    key = (request.client.host if request.client else 'unknown', 'login' if request.url.path == '/api/auth/login' else 'api')
    limit = 15 if key[1] == 'login' else 300
    with bucket_lock:
        stamp = time.monotonic()
        if len(buckets) > 10000:
            for stale in [k for k, v in buckets.items() if not v or v[-1] < stamp - 60]:
                del buckets[stale]
        queue = buckets[key]
        while queue and queue[0] < stamp - 60:
            queue.popleft()
        if len(queue) >= limit:
            return JSONResponse({'detail': 'Too many requests; try again in a minute'}, 429, headers={'Retry-After': '60'})
        queue.append(stamp)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Cache-Control'] = 'no-store'
    logger.info('%s %s %s %.0fms', request.method, request.url.path, response.status_code, (time.monotonic() - started) * 1000)
    return response


@app.exception_handler(IntegrityError)
async def conflict_handler(request, exc):
    return JSONResponse({'detail': 'A record already exists or conflicts with a related record'}, 409)


@app.get('/api/health')
def health():
    with engine.connect() as connection:
        connection.execute(text('SELECT 1'))
    return {'status': 'ok', 'version': '0.1.0'}
