from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.db.database import get_all_scans, delete_scan

router = APIRouter(prefix="/history", tags=["History"])

@router.get("/", response_model=List[Dict[str, Any]])
async def get_history():
    """Retrieve all currency scan history."""
    try:
        return get_all_scans()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{scan_id}")
async def remove_scan(scan_id: str):
    """Delete a scan from history."""
    try:
        delete_scan(scan_id)
        return {"success": True, "message": "Scan deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
