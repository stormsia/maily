from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/v1/config")
async def config(request: Request) -> dict[str, bool]:
    """Non-secret server facts for the dashboard (this router is auth-free)."""
    return {"api_key_required": bool(request.app.state.settings.api_key)}
