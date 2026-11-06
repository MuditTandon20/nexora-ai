"""Bound bytes as ASGI request chunks arrive, independently of Content-Length."""
import re
from starlette.responses import JSONResponse

MAX_BODY_BYTES = 11 * 1024 * 1024


class RequestBodyLimit:
    def __init__(self, app, max_bytes=MAX_BODY_BYTES):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        lengths = [value for key, value in scope['headers'] if key.lower() == b'content-length']
        if len(lengths) > 1 or (lengths and not re.fullmatch(rb'[0-9]+', lengths[0])):
            return await JSONResponse({'detail': 'Invalid Content-Length'}, 400)(scope, receive, send)
        # Avoid converting an arbitrarily large integer header.
        if lengths and (len(lengths[0]) > 20 or int(lengths[0]) > self.max_bytes):
            return await JSONResponse({'detail': 'Request too large'}, 413)(scope, receive, send)
        # Bound the body before downstream parsers/middleware can reclassify an
        # oversize receive exception as a generic 400. At most max_bytes are kept.
        body = bytearray()
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            chunk = message.get('body', b'')
            if len(body) + len(chunk) > self.max_bytes:
                return await JSONResponse({'detail': 'Request too large'}, 413)(scope, receive, send)
            body.extend(chunk)
            if not message.get('more_body', False):
                break
        replayed = False

        async def replay_receive():
            nonlocal replayed
            if not replayed:
                replayed = True
                return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
            return await receive()

        await self.app(scope, replay_receive, send)
