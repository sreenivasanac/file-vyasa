"""Health check utilities for LLM services."""

import httpx


async def check_llava_available() -> dict:
    """Check if Ollama llava model is available.

    Returns:
        dict with 'available' (bool) and 'reason' (str or None)
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code != 200:
                return {
                    "available": False,
                    "reason": "Ollama is not running. Start it with: ollama serve",
                }

            models = response.json().get("models", [])
            llava_available = any(
                m.get("name", "").startswith("llava") for m in models
            )

            if llava_available:
                return {"available": True, "reason": None}
            else:
                return {
                    "available": False,
                    "reason": "llava model not installed. Run: ollama pull llava",
                }

    except httpx.ConnectError:
        return {
            "available": False,
            "reason": "Cannot connect to Ollama. Start it with: ollama serve",
        }
    except Exception as e:
        return {"available": False, "reason": f"Error checking Ollama: {e}"}
