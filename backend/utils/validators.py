"""
backend/utils/validators.py — File and text input validation utilities
"""

import os
import hashlib
from typing import Tuple, Optional

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB


def allowed_file(filename: str) -> bool:
    """Check if the filename has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_extension(filename: str) -> str:
    """Extract the file extension from a filename."""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def compute_md5(file_stream) -> str:
    """Compute the MD5 checksum of a file stream without loading the whole file into memory."""
    hasher = hashlib.md5()
    # Ensure stream is read from the beginning
    file_stream.seek(0)
    for chunk in iter(lambda: file_stream.read(4096), b""):
        hasher.update(chunk)
    # Reset stream pointer for future reads
    file_stream.seek(0)
    return hasher.hexdigest()


def validate_uploaded_file(file_obj, filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate the uploaded file object.
    
    Returns:
        (is_valid, error_message)
    """
    if not file_obj or not filename:
        return False, "No file uploaded or filename is empty."

    # 1. Check extension
    if not allowed_file(filename):
        return False, f"Unsupported file type. Only {', '.join(ALLOWED_EXTENSIONS).upper()} files are allowed."

    # 2. Check size
    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(0)  # Reset pointer
    
    if size == 0:
        return False, "The uploaded file is empty."
        
    if size > MAX_FILE_SIZE:
        return False, f"File size exceeds the 16MB limit (found {(size / (1024 * 1024)):.2f}MB)."

    # 3. Check basic corruption for PDF files
    ext = get_file_extension(filename)
    if ext == 'pdf':
        header = file_obj.read(4)
        file_obj.seek(0)  # Reset pointer
        if header != b'%PDF':
            return False, "The PDF file appears to be corrupted or invalid."

    return True, None


def validate_text_input(title: str, text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate manual text copy-paste input.
    
    Returns:
        (is_valid, error_message)
    """
    if not title or not title.strip():
        return False, "Title is required and cannot be empty."
        
    if not text or not text.strip():
        return False, "Text content is required and cannot be empty."

    if len(text) > 1000000:
        return False, "Text content is too large (maximum 1,000,000 characters)."

    return True, None
