# app/middleware/mcp_session_wrapper.py
import json
import logging
from fastapi import Request
from typing import Any, Dict


logger = logging.getLogger("engine.mcp")


async def wrap_mcp_request_with_session(request: Request, original_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP request body'sine sessionId inject eder.
    
    Bu fonksiyon MCP'nin request handler'ından ÖNCE çalışır.
    """
    # Request state'den sessionId'yi al
    session_id = getattr(request.state, "injected_session_id", None)
    
    if session_id and "params" in original_body:
        if isinstance(original_body["params"], dict):
            if "sessionId" not in original_body["params"]:
                original_body["params"]["sessionId"] = session_id
                logger.info("✅ SessionId injected into params: %s for method=%s", 
                           session_id, original_body.get("method", "unknown"))
            else:
                logger.info("ℹ️ SessionId already exists in params")
        else:
            logger.warning("⚠️ params is not a dict, cannot inject sessionId")
    elif session_id:
        logger.warning("⚠️ No params in request body, cannot inject sessionId")
    
    return original_body
