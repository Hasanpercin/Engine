# app/mcp_sse.py
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import StreamingResponse
import asyncio, json

app = FastAPI()
channels: dict[str, asyncio.Queue] = {}

def auth_ok(authorization: str | None) -> bool:
    # Bearer kontrolünü buraya koy (örn. env'den karşılaştır)
    return authorization and authorization.startswith("Bearer ")

def get_sid(x_session_id: str | None, request: Request) -> str:
    sid = x_session_id or request.query_params.get("sessionId")
    if not sid:
        raise HTTPException(status_code=400, detail="Missing session ID")
    return sid

def chan(sid: str) -> asyncio.Queue:
    return channels.setdefault(sid, asyncio.Queue())

@app.get("/mcp/sse")
async def mcp_sse(request: Request,
                  authorization: str | None = Header(default=None),
                  x_session_id: str | None = Header(default=None)):
    if not auth_ok(authorization):
        raise HTTPException(status_code=401, detail="Missing/invalid Bearer token")
    sid = get_sid(x_session_id, request)
    q = chan(sid)

    async def eventgen():
        # açılış olayı
        yield f"event: open\ndata: {json.dumps({'sessionId': sid})}\n\n"
        while True:
            if await request.is_disconnected():
                break
            try:
                msg = await asyncio.wait_for(q.get(), timeout=25)
                yield f"event: message\ndata: {json.dumps(msg)}\n\n"
            except asyncio.TimeoutError:
                # keep-alive
                yield ":keepalive\n\n"

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"  # Nginx/Cloudflare buffering'i engeller
    }
    return StreamingResponse(eventgen(), media_type="text/event-stream", headers=headers)
