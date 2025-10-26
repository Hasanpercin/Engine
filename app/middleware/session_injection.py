# app/middleware/session_injection.py
"""
ASGI middleware for injecting X-Session-ID header into MCP request params.

This middleware works at the ASGI level (not HTTP middleware level),
which ensures reliable body modification without read conflicts.
"""
import json
import logging
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("engine.mcp")


class SessionIdInjectionMiddleware:
    """
    ASGI middleware that injects X-Session-ID header value into MCP params.sessionId
    
    Usage:
        app.add_middleware(SessionIdInjectionMiddleware)
    
    Example:
        Request Header: X-Session-ID: abc123
        Request Body (before): {"jsonrpc": "2.0", "method": "tools/call", "params": {...}}
        Request Body (after): {"jsonrpc": "2.0", "method": "tools/call", "params": {..., "sessionId": "abc123"}}
    """
    
    def __init__(self, app: ASGIApp):
        self.app = app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        # Only process HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Only process POST requests to MCP endpoints
        path = scope.get("path", "")
        method = scope.get("method", "")
        
        if path not in ["/mcp", "/sse"] or method != "POST":
            await self.app(scope, receive, send)
            return
        
        # Extract X-Session-ID header (case-insensitive)
        session_id = None
        for header_name, header_value in scope.get("headers", []):
            if header_name.lower() == b"x-session-id":
                session_id = header_value.decode("utf-8")
                break
        
        # No session ID in header, pass through unchanged
        if not session_id:
            await self.app(scope, receive, send)
            return
        
        # Collect body chunks
        body_parts = []
        
        async def wrapped_receive():
            message = await receive()
            
            if message["type"] == "http.request":
                body = message.get("body", b"")
                if body:
                    body_parts.append(body)
                
                # Last chunk - process the complete body
                if not message.get("more_body", False):
                    full_body = b"".join(body_parts)
                    
                    try:
                        # Parse JSON
                        body_json = json.loads(full_body.decode("utf-8"))
                        
                        # Inject sessionId into params if not already present
                        if "params" in body_json and isinstance(body_json["params"], dict):
                            if "sessionId" not in body_json["params"]:
                                body_json["params"]["sessionId"] = session_id
                                
                                logger.info(
                                    "✓ SessionId injected: %s for method=%s",
                                    session_id,
                                    body_json.get("method", "unknown")
                                )
                        
                        # Encode modified body
                        modified_body = json.dumps(body_json).encode("utf-8")
                        
                        return {
                            "type": "http.request",
                            "body": modified_body,
                            "more_body": False,
                        }
                    
                    except json.JSONDecodeError as e:
                        logger.warning("SessionId injection skipped: Invalid JSON - %s", str(e))
                        # Return original body on JSON error
                        return {
                            "type": "http.request",
                            "body": full_body,
                            "more_body": False,
                        }
                    
                    except Exception as e:
                        logger.error("SessionId injection error: %s", str(e), exc_info=True)
                        # Return original body on any error
                        return {
                            "type": "http.request",
                            "body": full_body,
                            "more_body": False,
                        }
                
                return message
            
            return message
        
        # Pass modified receive to the app
        await self.app(scope, wrapped_receive, send)
