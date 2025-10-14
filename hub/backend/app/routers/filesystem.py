"""
Filesystem browsing API for project selection
"""

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from app.schemas import FilesystemBrowseResponse

router = APIRouter(prefix="/filesystem", tags=["filesystem"])


@router.get("/home")
async def get_home_directory():
    """Get user's home directory"""
    home = str(Path.home())
    return {"path": home}


@router.get("/browse", response_model=FilesystemBrowseResponse)
async def browse_directory(path: str = Query(..., description="Directory path to browse")):
    """
    Browse filesystem directory

    Returns list of subdirectories for folder selection
    """
    try:
        # Normalize and validate path
        full_path = os.path.abspath(os.path.expanduser(path))

        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Path does not exist")

        if not os.path.isdir(full_path):
            raise HTTPException(status_code=400, detail="Path is not a directory")

        # Get parent directory
        parent = str(Path(full_path).parent) if full_path != "/" else None

        # List subdirectories
        directories = []
        try:
            for entry in sorted(os.listdir(full_path)):
                entry_path = os.path.join(full_path, entry)
                if os.path.isdir(entry_path) and not entry.startswith("."):
                    directories.append({"name": entry, "path": entry_path})
        except PermissionError:
            raise HTTPException(status_code=403, detail="Permission denied")

        return FilesystemBrowseResponse(
            currentPath=full_path, parent=parent, directories=directories
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
