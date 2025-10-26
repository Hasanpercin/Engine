# app/middleware/session_injection.py
import json
import logging
from starlette.requests import Request


logger = logging.getLogger("engine.mcp")


async def session_id_injection_middleware(request: Request, call_next):
    """
    HTTP middleware: X-Session-ID header'ından sessionId'yi okur ve MCP request body'sine ekler.
    
    Bu middleware, n8n gibi client'ların sessionId'yi header'da göndermesine izin verir,
    ve otomatik olarak MCP params'a ekler.
    """
    # Sadece MCP endpoint'leri için çalışsın
    if request.url.path in ["/mcp", "/sse"] and request.method == "POST":
        # Header'dan sessionId oku
        session_id = request.headers.get("X-Session-ID") or request.headers.get("x-session-id")
        
        logger.info("🔍 Middleware triggered: path=%s, method=%s, session_id=%s", 
                   request.url.path, request.method, session_id)
        
        if session_id:
            try:
                # Body'yi oku - DİKKAT: Sadece bir kere okunabilir!
                body_bytes = await request.body()
                
                logger.info("📦 Original body (first 200 chars): %s", body_bytes[:200])
                
                if body_bytes:
                    body_json = json.loads(body_bytes.decode('utf-8'))
                    
                    # SessionId injection
                    if "params" in body_json and isinstance(body_json["params"], dict):
                        if "sessionId" not in body_json["params"]:
                            body_json["params"]["sessionId"] = session_id
                            logger.info("✅ SessionId injected: %s for method=%s",
                                       session_id, body_json.get("method", "unknown"))
                        else:
                            logger.info("ℹ️ SessionId already exists in params, not injecting")
                    else:
                        logger.warning("⚠️ No params dict found in body, cannot inject")
                    
                    # Modified body'yi encode et
                    modified_body = json.dumps(body_json).encode('utf-8')
                    
                    # Request'in body'sini değiştirmek için yeni bir receive fonksiyonu oluştur
                    async def receive():
                        return {
                            "type": "http.request",
                            "body": modified_body,
                            "more_body": False,
                        }
                    
                    # Request'in scope'una yeni receive'i ata
                    request._receive = receive
                    
                    logger.info("📦 Modified body (first 200 chars): %s", modified_body[:200])
                    
            except json.JSONDecodeError as e:
                logger.warning("⚠️ JSON decode error: %s", e)
            except Exception as e:
                logger.error("❌ Injection error: %s", e, exc_info=True)
        else:
            logger.info("ℹ️ No X-Session-ID header found")
    
    # İşlemi devam ettir
    response = await call_next(request)
    return response
