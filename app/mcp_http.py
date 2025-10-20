# app/mcp_http.py (mevcut /mcp handler'ında uygun yere ekle)
from .mcp_sse import chan

async def handle_tool_call(session_id: str, name: str, arguments: dict, rpc_id: int):
    q = chan(session_id)

    if name == "engine.natal.chart_stream":
        # örnek: parça parça ilerleme/tok enler
        await q.put({"type": "progress", "step": "started"})
        for i in range(5):
            # burada gerçek hesaplama/LLM token'ı üret
            await asyncio.sleep(0.5)
            await q.put({"type": "delta", "text": f"parça-{i}"})
        await q.put({"type": "done"})
        # HTTP cevabı: SSE'ye geçtiğini söyle
        return {"status": "streaming", "via": "sse"}

    # streaming değilse normal senkron cevap:
    result = await run_sync_tool(name, arguments)
    return result
