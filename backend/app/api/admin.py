from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.db.database import get_stats

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats", response_model=Dict[str, Any])
async def admin_stats():
    """Retrieve statistics for the admin dashboard."""
    try:
        return get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
