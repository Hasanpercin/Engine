# --------- MCP SessionId Injection Middleware (ASGI Version - %100 Garantili) ---------
class SessionIdInjectionMiddleware:
    """
    ASGI middleware - Body'yi düzgün şekilde handle eder.
    BaseHTTPMiddleware'den daha low-level ama daha güvenilir.
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
        
        if path not in ["/mcp", "/sse"] or method != "POST":
            await self.app(scope, receive, send)
            return
        
        # Header'dan sessionId bul
        session_id = None
        for header_name, header_value in scope.get("headers", []):
            if header_name.lower() == b"x-session-id":
                session_id = header_value.decode('utf-8')
                break
        
        if not session_id:
            # SessionId yoksa normal devam et
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
                    
                    try:
                        body_json = json.loads(full_body.decode('utf-8'))
                        
                        # SessionId injection
                        if "params" in body_json and isinstance(body_json["params"], dict):
                            if "sessionId" not in body_json["params"]:
                                body_json["params"]["sessionId"] = session_id
                                self.logger.info(
                                    "✓ SessionId injected: %s for method=%s",
                                    session_id,
                                    body_json.get("method", "unknown")
                                )
                        
                        # Modified body'yi döndür
                        modified_body = json.dumps(body_json).encode('utf-8')
                        return {
                            "type": "http.request",
                            "body": modified_body,
                            "more_body": False,
                        }
                    
                    except Exception as e:
                        self.logger.error("SessionId injection failed: %s", e, exc_info=True)
                        # Hata durumunda orijinal body'yi dön
                        return {
                            "type": "http.request",
                            "body": full_body,
                            "more_body": False,
                        }
                
                return message
            
            return message
        
        await self.app(scope, wrapped_receive, send)


# Middleware'i ekle (BaseHTTPMiddleware YERINE bunu kullan)
app.add_middleware(SessionIdInjectionMiddleware)
