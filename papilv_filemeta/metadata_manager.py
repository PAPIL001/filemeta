# from typing import Dict, Any, List, Optional # Import Optional
# import os
# import json
# from sqlalchemy.orm import Session, joinedload
# from sqlalchemy.exc import IntegrityError, NoResultFound
# from datetime import datetime
# from sqlalchemy import func, or_, String

# from .models import File, Tag
# from .utils import infer_metadata, parse_tag_value

# # Important: This file (metadata_manager.py) should NOT import
# # 'engine', 'Base', or 'get_db' from '.database'.
# # Its functions receive a 'Session' object directly via FastAPI's Depends.

# def add_file_metadata(db: Session, filepath: str, custom_tags: Dict[str, Any]) -> File:
#     """
#     Adds new file metadata and associated custom tags to the database.
#     """
#     if not os.path.exists(filepath):
#         raise FileNotFoundError(f"File not found at: {filepath}")

#     existing_file = db.query(File).filter(File.filepath == filepath).first()
#     if existing_file:
#         raise ValueError(f"Metadata for file '{filepath}' already exists (ID: {existing_file.id}). Use 'update' to modify.")

#     inferred_data = infer_metadata(filepath)

#     file_record = File(
#         filename=os.path.basename(filepath),
#         filepath=filepath,
#         owner=inferred_data.get('os_owner'),
#         created_by="system",
#         created_at=datetime.now(),
#         updated_at=datetime.now(),
#         # Store as Python dictionary; SQLAlchemy's JSONB type handles serialization
#         inferred_tags=inferred_data # CHANGE: Removed json.dumps()
#     )
#     db.add(file_record)
#     db.flush() # Flush to get the file_record.id before adding tags

#     for key, value in custom_tags.items():
#         # Ensure value is converted to string if necessary, but keep original type for 'value_type'
#         typed_value, value_type = parse_tag_value(str(value)) # parse_tag_value should handle input, ensuring it returns string for value

#         # Check if value_dict is expected if 'value' is nested
#         # Based on your FileCreate model, custom_tags are Dict[str, Any], so value should be direct
#         # Assuming parse_tag_value returns actual typed_value (e.g., int, bool, str) and value_type (e.g., 'integer', 'boolean', 'string')
        
#         tag_record = Tag(
#             file_id=file_record.id,
#             key=key,
#             value=str(typed_value), # Ensure value is stored as string in DB
#             value_type=value_type
#         )
#         db.add(tag_record)

#     try:
#         db.commit()
#         # IMPORTANT: Eager load the tags directly before returning.
#         # db.refresh(file_record) alone won't eager-load relationships.
#         # Re-query with joinedload.
#         file_record_with_tags = db.query(File).options(joinedload(File.tags)).filter(File.id == file_record.id).first()
#         return file_record_with_tags
#     except IntegrityError as e:
#         db.rollback()
#         if "duplicate key value violates unique constraint" in str(e): # Specific PostgreSQL error
#             existing_file_on_error = db.query(File).filter(File.filepath == filepath).first()
#             existing_id_msg = f"(ID: {existing_file_on_error.id})" if existing_file_on_error else ""
#             raise ValueError(f"Metadata for file '{filepath}' already exists {existing_id_msg}. Use 'update' to modify.")
#         else:
#             raise Exception(f"Database integrity error: {e}. Check database constraints.")
#     except Exception as e:
#         db.rollback()
#         raise Exception(f"An unexpected error occurred while adding file metadata: {e}")

# def get_file_metadata(db: Session, file_id: int) -> File:
#     """
#     Retrieves file metadata by its ID, eager loading tags.
#     """
#     # FIX: Added joinedload(File.tags) for single file retrieval
#     file_record = db.query(File).options(joinedload(File.tags)).filter(File.id == file_id).first()
#     if not file_record:
#         raise NoResultFound(f"No metadata found for file ID: {file_id}")
#     return file_record

# def list_files(db: Session) -> List[File]:
#     """
#     Lists all file metadata records in the database, eager loading tags.
#     """
#     # This was already correct from previous iterations
#     return db.query(File).options(joinedload(File.tags)).all()

# def search_files(db: Session, keywords: List[str]) -> List[File]:
#     """
#     Searches for files based on keywords across various fields, eager loading tags.
#     """
#     if not keywords:
#         return []

#     search_conditions = []
#     for keyword in keywords:
#         search_pattern = f"%{keyword.lower()}%"

#         search_conditions.append(func.lower(File.filename).like(search_pattern))
#         search_conditions.append(func.lower(File.filepath).like(search_pattern))
#         search_conditions.append(func.lower(File.owner).like(search_pattern))
#         search_conditions.append(func.lower(File.created_by).like(search_pattern))

#         # Search within inferred_tags (JSONB) - Casting to String for LIKE operator
#         search_conditions.append(func.lower(File.inferred_tags.cast(String)).like(search_pattern))

#         # Search within custom tags (key and value)
#         search_conditions.append(
#             File.tags.any(
#                 or_(
#                     func.lower(Tag.key).like(search_pattern),
#                     func.lower(Tag.value).like(search_pattern)
#                 )
#             )
#         )

#     # FIX: Added joinedload(File.tags) for search results
#     return db.query(File).options(joinedload(File.tags)).filter(or_(*search_conditions)).distinct().all()


# def update_file_tags(
#     db: Session,
#     file_id: int,
#     tags_to_add_modify: Optional[Dict[str, Any]] = None,
#     tags_to_remove: Optional[List[str]] = None,
#     new_filepath: Optional[str] = None, # Added Optional
#     overwrite_existing: bool = False
# ) -> File:
#     """
#     Updates metadata (tags and/or filepath) for a specific file.
#     """
#     # Eager load tags here too, as they might be needed for modification or removal logic
#     file_record = db.query(File).options(joinedload(File.tags)).filter(File.id == file_id).first()
#     if not file_record:
#         raise NoResultFound(f"No metadata found for file ID: {file_id}")

#     try:
#         # 1. Handle File Path Update
#         if new_filepath:
#             if not os.path.exists(new_filepath):
#                 raise ValueError(f"New file path '{new_filepath}' does not exist on the filesystem. Cannot update path.")
            
#             # Check for existing file with the new_filepath to prevent unique constraint violation
#             existing_file_at_new_path = db.query(File).filter(File.filepath == new_filepath, File.id != file_id).first()
#             if existing_file_at_new_path:
#                 # If overwrite_existing allows, you'd delete/handle the existing record.
#                 # For now, it's a conflict unless you have a more complex merge strategy.
#                 raise ValueError(f"File metadata for '{new_filepath}' already exists (ID: {existing_file_at_new_path.id}). Cannot update path due to conflict.")
            
#             file_record.filepath = new_filepath
#             file_record.filename = os.path.basename(new_filepath) # Update filename if path changes

#         # 2. Handle Tag Removals/Overwrites
#         if overwrite_existing:
#             # If overwrite is true, delete ALL existing custom tags for this file
#             db.query(Tag).filter(Tag.file_id == file_id).delete(synchronize_session=False)
#             db.flush() # Ensure deletions are processed before adding new ones
#         else:
#             # If not overwriting, handle specific tag removals
#             if tags_to_remove:
#                 # Ensure tags_to_remove only contains strings (keys)
#                 db.query(Tag).filter(
#                     Tag.file_id == file_id,
#                     Tag.key.in_(tags_to_remove)
#                 ).delete(synchronize_session=False)
#                 db.flush() # Flush to ensure these are removed before potential re-add/update

#         # 3. Handle Tags to Add/Modify
#         if tags_to_add_modify:
#             for key, value in tags_to_add_modify.items():
#                 existing_tag = db.query(Tag).filter(Tag.file_id == file_id, Tag.key == key).first()
#                 typed_value, value_type = parse_tag_value(str(value)) # Always parse value for type

#                 if existing_tag:
#                     # Modify existing tag's value and type
#                     existing_tag.value = str(typed_value)
#                     existing_tag.value_type = value_type
#                 else:
#                     # Add new tag
#                     tag_record = Tag(
#                         file_id=file_record.id,
#                         key=key,
#                         value=str(typed_value),
#                         value_type=value_type
#                     )
#                     db.add(tag_record)

#         # 4. Update the file's updated_at timestamp
#         file_record.updated_at = datetime.now()

#         db.add(file_record) # Mark the file_record as modified if changes were made
#         db.commit()
#         # Re-query with joinedload to ensure the returned file_record has its tags loaded
#         db.refresh(file_record) # Refresh state from DB, needed before joinedload
#         file_record_with_tags = db.query(File).options(joinedload(File.tags)).filter(File.id == file_record.id).first()
#         return file_record_with_tags
#     except NoResultFound:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise Exception(f"An unexpected error occurred while updating file metadata for ID {file_id}: {e}")

# def delete_file_metadata(db: Session, file_id: int):
#     """
#     Deletes file metadata and its associated tags from the database.
#     """
#     file_record = db.query(File).filter(File.id == file_id).first()
#     if not file_record:
#         raise NoResultFound(f"No metadata found for file ID: {file_id}")

#     try:
#         db.delete(file_record)
#         db.commit()
#     except NoResultFound:
#         db.rollback()
#         raise
#     except Exception as e:
#         db.rollback()
#         raise Exception(f"An unexpected error occurred while deleting metadata for file ID {file_id}: {e}")
from typing import Dict, Any, List, Optional # Import Optional
import os
import json
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, NoResultFound
from datetime import datetime
from sqlalchemy import func, or_, String, Integer # Import Integer for casting

from .models import File, Tag, User # Import User model to reference its ID
from .utils import infer_metadata, parse_tag_value

# Important: This file (metadata_manager.py) should NOT import
# 'engine', 'Base', or 'get_db' from '.database'.
# Its functions receive a 'Session' object directly via FastAPI's Depends.

def add_file_metadata(
    db: Session,
    filepath: str,
    custom_tags: Dict[str, Any],
    owner_id: Optional[int] = None, # New: Accept owner_id
    created_by: Optional[str] = None # New: Accept created_by
) -> File:
    """
    Adds new file metadata and associated custom tags to the database.
    Associates the file with the provided owner_id.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found at: {filepath}")

    existing_file = db.query(File).filter(File.filepath == filepath).first()
    if existing_file:
        raise ValueError(f"Metadata for file '{filepath}' already exists (ID: {existing_file.id}). Use 'update' to modify.")

    inferred_data = infer_metadata(filepath)

    file_record = File(
        filename=os.path.basename(filepath),
        filepath=filepath,
        # FIX: Assign owner_id directly from the authenticated user
        owner=owner_id,
        # FIX: Assign created_by from the authenticated user
        created_by=created_by if created_by else "system", # Use provided created_by or default
        created_at=datetime.now(),
        updated_at=datetime.now(),
        inferred_tags=inferred_data
    )
    db.add(file_record)
    db.flush() # Flush to get the file_record.id before adding tags

    for key, value in custom_tags.items():
        typed_value, value_type = parse_tag_value(str(value)) # parse_tag_value should handle input, ensuring it returns string for value

        tag_record = Tag(
            file_id=file_record.id,
            key=key,
            value=str(typed_value), # Ensure value is stored as string in DB
            value_type=value_type
        )
        db.add(tag_record)

    try:
        db.commit()
        # IMPORTANT: Eager load the tags directly before returning.
        # Re-query with joinedload.
        file_record_with_tags = db.query(File).options(joinedload(File.tags)).filter(File.id == file_record.id).first()
        return file_record_with_tags
    except IntegrityError as e:
        db.rollback()
        if "duplicate key value violates unique constraint" in str(e).lower() and "file_filepath_key" in str(e).lower():
            # More specific check for filepath uniqueness violation
            existing_file_on_error = db.query(File).filter(File.filepath == filepath).first()
            existing_id_msg = f"(ID: {existing_file_on_error.id})" if existing_file_on_error else ""
            raise ValueError(f"Metadata for file '{filepath}' already exists {existing_id_msg}. Use 'update' to modify.")
        elif "null value in column \"owner\" violates not-null constraint" in str(e).lower() and owner_id is None:
            raise ValueError("Owner ID cannot be null. Please ensure a user is logged in.")
        else:
            raise Exception(f"Database integrity error: {e}. Check database constraints.")
    except Exception as e:
        db.rollback()
        raise Exception(f"An unexpected error occurred while adding file metadata: {e}")

def get_file_metadata(db: Session, file_id: int) -> File:
    """
    Retrieves file metadata by its ID, eager loading tags.
    """
    file_record = db.query(File).options(joinedload(File.tags)).filter(File.id == file_id).first()
    if not file_record:
        raise NoResultFound(f"No metadata found for file ID: {file_id}")
    return file_record

def list_files(db: Session, owner_id: Optional[int] = None) -> List[File]: # New: Optional owner_id
    """
    Lists all file metadata records in the database, eager loading tags.
    Optionally filters by owner_id.
    """
    query = db.query(File).options(joinedload(File.tags))
    if owner_id is not None:
        query = query.filter(File.owner == owner_id) # Filter by owner if provided
    return query.all()

def search_files(db: Session, keywords: List[str], owner_id: Optional[int] = None) -> List[File]: # New: Optional owner_id
    """
    Searches for files based on keywords across various fields, eager loading tags.
    Optionally filters by owner_id.
    """
    if not keywords:
        # If no keywords, but an owner_id is provided, still list by owner.
        # Otherwise, return empty list or all files (depending on intent)
        if owner_id is not None:
            return list_files(db, owner_id=owner_id)
        return []

    search_conditions = []
    for keyword in keywords:
        search_pattern = f"%{keyword.lower()}%"

        search_conditions.append(func.lower(File.filename).like(search_pattern))
        search_conditions.append(func.lower(File.filepath).like(search_pattern))
        # REMOVED: func.lower(File.owner).like(search_pattern) - Owner is an Integer ID
        search_conditions.append(func.lower(File.created_by).like(search_pattern))

        # Search within inferred_tags (JSONB) - Casting to String for LIKE operator
        # This will search values within the JSONB. For keys, you might need specific JSONB operators.
        search_conditions.append(func.lower(File.inferred_tags.astext).like(search_pattern))


        # Search within custom tags (key and value)
        search_conditions.append(
            File.tags.any(
                or_(
                    func.lower(Tag.key).like(search_pattern),
                    func.lower(Tag.value).like(search_pattern)
                )
            )
        )

    query = db.query(File).options(joinedload(File.tags)).filter(or_(*search_conditions))

    # FIX: Add owner_id filter to the search query if provided
    if owner_id is not None:
        query = query.filter(File.owner == owner_id)

    return query.distinct().all()


def update_file_tags(
    db: Session,
    file_id: int,
    tags_to_add_modify: Optional[Dict[str, Any]] = None,
    tags_to_remove: Optional[List[str]] = None,
    new_filepath: Optional[str] = None,
    overwrite_existing: bool = False
) -> File:
    """
    Updates metadata (tags and/or filepath) for a specific file.
    """
    # Eager load tags here too, as they might be needed for modification or removal logic
    file_record = db.query(File).options(joinedload(File.tags)).filter(File.id == file_id).first()
    if not file_record:
        raise NoResultFound(f"No metadata found for file ID: {file_id}")

    try:
        # 1. Handle File Path Update
        if new_filepath:
            if not os.path.exists(new_filepath):
                raise ValueError(f"New file path '{new_filepath}' does not exist on the filesystem. Cannot update path.")
            
            # Check for existing file with the new_filepath to prevent unique constraint violation
            existing_file_at_new_path = db.query(File).filter(File.filepath == new_filepath, File.id != file_id).first()
            if existing_file_at_new_path:
                raise ValueError(f"File metadata for '{new_filepath}' already exists (ID: {existing_file_at_new_path.id}). Cannot update path due to conflict.")
            
            file_record.filepath = new_filepath
            file_record.filename = os.path.basename(new_filepath) # Update filename if path changes

        # 2. Handle Tag Removals/Overwrites
        if overwrite_existing:
            # If overwrite is true, delete ALL existing custom tags for this file
            db.query(Tag).filter(Tag.file_id == file_id).delete(synchronize_session=False)
            db.flush() # Ensure deletions are processed before adding new ones
        else:
            # If not overwriting, handle specific tag removals
            if tags_to_remove:
                # Ensure tags_to_remove only contains strings (keys)
                db.query(Tag).filter(
                    Tag.file_id == file_id,
                    Tag.key.in_(tags_to_remove)
                ).delete(synchronize_session=False)
                db.flush() # Flush to ensure these are removed before potential re-add/update

        # 3. Handle Tags to Add/Modify
        if tags_to_add_modify:
            for key, value in tags_to_add_modify.items():
                existing_tag = db.query(Tag).filter(Tag.file_id == file_id, Tag.key == key).first()
                typed_value, value_type = parse_tag_value(str(value)) # Always parse value for type

                if existing_tag:
                    # Modify existing tag's value and type
                    existing_tag.value = str(typed_value)
                    existing_tag.value_type = value_type
                else:
                    # Add new tag
                    tag_record = Tag(
                        file_id=file_record.id,
                        key=key,
                        value=str(typed_value),
                        value_type=value_type
                    )
                    db.add(tag_record)

        # 4. Update the file's updated_at timestamp
        file_record.updated_at = datetime.now()

        db.add(file_record) # Mark the file_record as modified if changes were made
        db.commit()
        # Re-query with joinedload to ensure the returned file_record has its tags loaded
        db.refresh(file_record) # Refresh state from DB, needed before joinedload
        file_record_with_tags = db.query(File).options(joinedload(File.tags)).filter(File.id == file_record.id).first()
        return file_record_with_tags
    except NoResultFound:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise Exception(f"An unexpected error occurred while updating file metadata for ID {file_id}: {e}")

def delete_file_metadata(db: Session, file_id: int):
    """
    Deletes file metadata and its associated tags from the database.
    """
    file_record = db.query(File).filter(File.id == file_id).first()
    if not file_record:
        raise NoResultFound(f"No metadata found for file ID: {file_id}")

    try:
        db.delete(file_record)
        db.commit()
    except NoResultFound:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise Exception(f"An unexpected error occurred while deleting metadata for file ID {file_id}: {e}")