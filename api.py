from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound, IntegrityError
from typing import List, Optional, Dict, Any
import os
import json
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Corrected absolute imports for models and manager functions
from papilv_filemeta.database import init_db, get_db
from papilv_filemeta.metadata_manager import (
    add_file_metadata,
    list_files,
    get_file_metadata,
    search_files,
    update_file_tags,
    delete_file_metadata
)
# Alias to avoid conflict with Pydantic 'File' and 'Tag' used in responses
from papilv_filemeta.models import File as DBFile, Tag as DBTag

# --- Pydantic Models for API Request/Response ---

# Tag model for response
class TagResponse(BaseModel):
    key: str
    value: str
    value_type: str

    class Config:
        from_attributes = True


# File model for response
class FileResponse(BaseModel):
    id: int
    filename: str
    filepath: str
    owner: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    inferred_tags: Optional[Dict[str, Any]] = None # Should be a dictionary
    tags: List['TagResponse'] = [] # List of TagResponse objects

    # Validator to handle potential stringified JSON from older DB entries or inconsistent data
    # This remains useful if the DB might contain 'inferred_tags' as a JSON string for some reason.
    @validator('inferred_tags', pre=True, always=True)
    def parse_inferred_tags(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # If it's a string but not valid JSON, return an empty dict or handle as appropriate
                return {}
        return v

    class Config:
        from_attributes = True
        json_dumps = json.dumps # Good practice for Pydantic and JSON


# Model for adding file metadata (request body)
class FileCreate(BaseModel):
    filepath: str
    custom_tags: Dict[str, Any] = {} # Default to empty dict is good


# Model for updating file metadata (request body)
class FileUpdate(BaseModel):
    tags_to_add_modify: Optional[Dict[str, Any]] = None
    tags_to_remove: Optional[List[str]] = None # Corrected typo here
    new_filepath: Optional[str] = None
    overwrite_existing: bool = False


# Model for search query (query parameters)
class FileSearchQuery(BaseModel):
    # Changed to 'str' to easily accept comma-separated keywords from URL
    keywords: str = Field(..., description="Comma-separated keywords to search for")


# --- FastAPI Application Instance ---
app = FastAPI(
    title="File Metadata API",
    description="API for managing file metadata.",
    version="1.0.0"
)

# --- Startup Event: Initialize Database ---
@app.on_event("startup")
def on_startup():
    """Initializes the database when the FastAPI application starts."""
    print("FastAPI app starting up: Initializing database...")
    try:
        init_db()
        print("Database initialization complete.")
    except Exception as e:
        print(f"Error during database initialization: {e}")


# --- API Endpoints ---

@app.get("/")
async def root():
    return {"message": "Welcome to the File Metadata API! Visit /docs for API documentation."}

@app.post("/files/", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def create_file_metadata(file_data: FileCreate):
    """
    Adds new metadata for a file.
    """
    try:
        with get_db() as db: # Manual session management using context manager
            file_record = add_file_metadata(db, file_data.filepath, file_data.custom_tags)
            return file_record
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e: # For cases like file already exists
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to add file metadata: {e}")

@app.get("/files/", response_model=List[FileResponse])
async def read_files():
    """
    Lists all stored file metadata.
    """
    try:
        with get_db() as db: # Manual session management using context manager
            files = list_files(db)
            return files
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve files: {e}")

@app.get("/files/{file_id}", response_model=FileResponse)
async def read_file_metadata(file_id: int):
    """
    Retrieves metadata for a specific file by ID.
    """
    try:
        with get_db() as db: # Manual session management using context manager
            file_record = get_file_metadata(db, file_id)
            # get_file_metadata now raises NoResultFound directly,
            # so this check can be slightly simplified or removed if preferred
            if file_record is None: # In case get_file_metadata returns None before raising
                raise NoResultFound(f"File with ID {file_id} not found")
            return file_record
    except NoResultFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve file metadata: {e}")

@app.get("/files/search/", response_model=List[FileResponse])
async def search_file_metadata(query: FileSearchQuery = Depends()):
    """
    Searches for files based on keywords across various metadata fields.
    Keywords should be provided as a comma-separated string in the query parameter.
    Example: /files/search/?keywords=report,finance
    """
    # Parse the comma-separated string into a list
    keywords_list = [k.strip() for k in query.keywords.split(',') if k.strip()]

    try:
        with get_db() as db: # Manual session management using context manager
            files = search_files(db, keywords_list)
            return files
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to perform search: {e}")


@app.put("/files/{file_id}", response_model=FileResponse)
async def update_file_metadata(
    file_id: int,
    update_data: FileUpdate,
):
    """
    Updates metadata (tags, filepath) for a specific file.
    """
    try:
        with get_db() as db: # Manual session management using context manager
            updated_file = update_file_tags(
                db,
                file_id,
                tags_to_add_modify=update_data.tags_to_add_modify,
                tags_to_remove=update_data.tags_to_remove, # This now uses the corrected name
                new_filepath=update_data.new_filepath,
                overwrite_existing=update_data.overwrite_existing
            )
            return updated_file
    except NoResultFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e: # For invalid input or conflicts
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update file metadata: {e}")

@app.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_metadata_api(file_id: int):
    """
    Deletes metadata for a specific file by ID.
    """
    try:
        with get_db() as db: # Manual session management using context manager
            delete_file_metadata(db, file_id)
            # FastAPI's 204 No Content typically doesn't return a body.
            # Returning an empty dictionary is usually fine for 204.
            return {}
    except NoResultFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete file metadata: {e}")