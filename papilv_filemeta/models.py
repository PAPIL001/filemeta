from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import json # For handling JSONB default values (though SQLAlchemy's JSONB type handles this well)
from .database import Base # Correct: Assumes database.py defines Base and is in the same package

# --- User Model ---
# You need a User model to store user information, especially for owner and authentication.
class User(Base):
    __tablename__ = 'user' # Use 'user' for consistency with ForeignKey in File model

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False) # e.g., 'user', 'admin'
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

    # Define relationship from User to File (one-to-many: one user can own many files)
    files = relationship("File", back_populates="owner_rel", cascade="all, delete-orphan") # cascade ensures files are deleted if user is deleted, or adjust as needed

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

# --- File Model ---
class File(Base):
    __tablename__ = 'file' # Changed from 'files' to 'file' for consistency with ForeignKey

    id = Column(Integer, primary_key=True, index=True) # Added index=True for better lookup performance
    filename = Column(String(255), nullable=False)
    filepath = Column(Text, nullable=False, unique=True) # Added unique=True as filepath should be unique

    # OWNER FIELD: CRITICAL CHANGE
    # Changed from String(255) to Integer and added ForeignKey to User.id
    owner = Column(Integer, ForeignKey('user.id'), nullable=True) # Nullable=True if a file can exist without an owner, or False if owner is always required
    owner_rel = relationship("User", back_populates="files") # Relationship to the User model

    created_by = Column(String(255), nullable=False) # Stores the username string of who created it (e.g., 'system' or 'admin_user')
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now, nullable=False) # Corrected name to updated_at as used in Pydantic
    
    inferred_tags = Column(JSONB, default=lambda: {}, nullable=False) # Correct: JSONB type handles dicts directly

    # Define relationship from File to Tag (one-to-many: one file can have many tags)
    tags = relationship("Tag", back_populates="file", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<File(id={self.id}, filename='{self.filename}', filepath='{self.filepath}', owner_id={self.owner})>"

    # The to_dict method is no longer strictly necessary if you're using Pydantic's from_attributes=True
    # However, it can be useful for debugging or specific internal conversions.
    # I'll keep it, but simplify it based on Pydantic's needs.
    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "filepath": self.filepath,
            "owner": self.owner, # Owner ID (int)
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "inferred_tags": self.inferred_tags if self.inferred_tags is not None else {}, # Ensure it's dict
            # For 'tags', Pydantic's from_attributes will handle the relationship load
            # If you *must* flatten tags here, you'd do:
            "tags": [tag.to_dict() for tag in self.tags] if self.tags else [] # Needs Tag.to_dict()
        }


# --- Tag Model ---
class Tag(Base):
    __tablename__ = 'tag' # Changed from 'tags' to 'tag' for consistency

    id = Column(Integer, primary_key=True, index=True) # Added index=True
    file_id = Column(Integer, ForeignKey('file.id', ondelete='CASCADE'), nullable=False) # Changed 'files.id' to 'file.id'
    key = Column(String(255), nullable=False) # Increased length for keys
    value = Column(Text, nullable=False) # Storing value as string
    value_type = Column(String(50), nullable=False) # Store original Python type, e.g., 'str', 'int', 'bool', 'float'

    # Define relationship from Tag to File (many-to-one: many tags belong to one file)
    file = relationship("File", back_populates="tags")

    # Add a unique constraint to prevent duplicate tags (key) for the same file
    __table_args__ = (UniqueConstraint('file_id', 'key', name='_file_key_uc'),)

    def __repr__(self):
        return f"<Tag(id={self.id}, file_id={self.file_id}, key='{self.key}', value='{self.value}', type='{self.value_type}')>"

    # This get_typed_value method is helpful for internal logic but not strictly needed for Pydantic response
    def get_typed_value(self):
        """Converts the stored string value back to its original Python type."""
        if self.value_type == 'int':
            try:
                return int(self.value)
            except ValueError:
                return None # Or raise an error
        elif self.value_type == 'float':
            try:
                return float(self.value)
            except ValueError:
                return None
        elif self.value_type == 'bool':
            return self.value.lower() == 'true'
        elif self.value_type == 'NoneType':
            return None
        return self.value # Default to string

    # Add a to_dict method for Tag if File.to_dict needs to flatten tags
    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value, # Stored as string, Pydantic TagResponse expects str
            "value_type": self.value_type
        }