# app/middleware/session_injection.py
import json
import logging


class SessionIdInjectionMiddleware:
    """
    ASGI middleware - X-Session-ID header'ından sessionId'yi okur ve MCP request body'sine ekler.
    """
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("engine.mcp")

    async def __call__(self, scope, receive, send):
        # Sadece HTTP POST isteklerini işle
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Path kontrolü
        path = scope.get("path", "")
        method = scope.get("method", "")
        
        # DEBUG: Her /mcp isteğini logla
        if path in ["/mcp", "/sse"]:
            self.logger.info("🔍 Middleware triggered: path=%s, method=%s", path, method)
        
        if path not in ["/mcp", "/sse"] or method != "POST":
            await self.app(scope, receive, send)
            return
        
        # Header'dan sessionId bul
        session_id = None
        headers = scope.get("headers", [])
        
        # DEBUG: Tüm header'ları logla
        self.logger.info("📋 Headers received: %s", 
                        [(h[0].decode(), h[1].decode()) for h in headers if h[0].lower() == b"x-session-id"])
        
        for header_name, header_value in headers:
            if header_name.lower() == b"x-session-id":
                session_id = header_value.decode('utf-8')
                self.logger.info("✓ Found X-Session-ID header: %s", session_id)
                break
        
        if not session_id:
            # SessionId yoksa uyar
            self.logger.warning("⚠️ No X-Session-ID header found, skipping injection")
            await self.app(scope, receive, send)
            return
        
        # Body'yi topla
        body_parts = []
        
        async def wrapped_receive():
            message = await receive()
            if message["type"] == "http.request":
                body_parts.append(message.get("body", b""))
                
                # Son parça mı?
                if not message.get("more_body", False):
                    # Tüm body toplandı, işle
                    full_body = b"".join(body_parts)
                    
                    # DEBUG: Body'yi logla
                    self.logger.info("📦 Original body: %s", full_body[:200])  # İlk 200 char
                    
                    try:
                        body_json = json.loads(full_body.decode('utf-8'))
                        
                        # SessionId injection
                        if "params" in body_json and isinstance(body_json["params"], dict):
                            if "sessionId" not in body_json["params"]:
                                body_json["params"]["sessionId"] = session_id
                                self.logger.info(
                                    "✅ SessionId injected: %s for method=%s",
                                    session_id,
                                    body_json.get("method", "unknown")
                                )
                            else:
                                self.logger.info("ℹ️ SessionId already exists in params, not injecting")
                        else:
                            self.logger.warning("⚠️ No params dict found in body, cannot inject")
                        
                        # Modified body'yi döndür
                        modified_body = json.dumps(body_json).encode('utf-8')
                        
                        # DEBUG: Modified body'yi logla
                        self.logger.info("📦 Modified body: %s", modified_body[:200])
                        
                        return {
                            "type": "http.request",
                            "body": modified_body,
                            "more_body": False,
                        }
                    
                    except Exception as e:
                        self.logger.error("❌ SessionId injection failed: %s", e, exc_info=True)
                        # Hata durumunda orijinal body'yi dön
                        return {
                            "type": "http.request",
                            "body": full_body,
                            "more_body": False,
                        }
                
                return message
            
            return message
        
        await self.app(scope, wrapped_receive, send)
