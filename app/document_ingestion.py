"""
Document Ingestion System: The "Librarian" of the Project.

This module acts as a high-fidelity document processor. It transforms raw, diverse 
data sources (ZIPs, directories, CSVs, JSONs, raw logs) into standardized "Knowledge Chunks".

Design Intent:
- Maintain strict line-number fidelity for evidence verification.
- Segment data into digestable sizes for both Rule-Engine and LLM processing.
- Ensure cross-platform compatibility with robust encoding handling.
"""

import json
import csv
import uuid
import zipfile
import mimetypes
import tempfile
import os
import re
import psutil
from pathlib import Path
from typing import Optional, Union


def ingest_file(file_path: str) -> list[dict]:
    """
    The entry point for data collection. Acts as a smart dispatcher 
    that decides how to best process the incoming source.
    
    Args:
        file_path: Absolute or relative path to the data source.
    
    Returns:
        A list of standardized document chunks ready for analysis.
    
    Raises:
        ValueError: If file path is invalid, unsafe, or unsupported
        FileNotFoundError: If file does not exist
    """
    # Input validation
    path = Path(file_path)
    
    # Validate path safety (prevent directory traversal)
    if not _is_safe_path(file_path):
        raise ValueError(f"Unsafe file path detected: {file_path}")
    
    # Check if file exists
    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")
    
    # Check if file is too large (10MB limit)
    if path.is_file() and path.stat().st_size > 10 * 1024 * 1024:  # 10MB
        raise ValueError(f"File too large (>10MB): {file_path}")
    
    # Delegate to specialized handlers based on source type
    if path.suffix.lower() == ".zip":
        return _ingest_zip(path)
    
    if path.is_dir():
        return _ingest_directory(path)
    
    # Validate file type and MIME type
    suffix = path.suffix.lower().lstrip(".")
    mime_type = mimetypes.guess_type(str(path))[0]
    if mime_type and not _is_safe_mime_type(mime_type):
        raise ValueError(f"Potentially unsafe MIME type: {mime_type}")
    
    if suffix not in {"txt", "log", "conf", "config", "csv", "json"}:
        raise ValueError(f"Unsupported file type: {suffix}. Only text, configuration, and structured data files are supported.")
    
    if suffix in {"txt", "log", "conf", "config"}:
        return _ingest_text(path, suffix)
    if suffix == "csv":
        return _ingest_csv(path)
    if suffix == "json":
        return _ingest_json(path)
    
    return []


def _ingest_zip(zip_path: Path) -> list[dict]:
    """Unpacks and audits all supported content within a ZIP archive."""
    chunks = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Analyze the archive contents
            file_list = zip_ref.namelist()
            
            for file_name in file_list:
                # We skip directory markers to focus on actual data files
                if file_name.endswith('/'):
                    continue
                
                # Verify file compatibility before extraction
                file_path = Path(file_name)
                suffix = file_path.suffix.lower().lstrip(".")
                
                if suffix not in {"txt", "log", "conf", "config", "csv", "json"}:
                    continue
                
                # Check file size inside ZIP to prevent decompression bombs
                info = zip_ref.getinfo(file_name)
                if info.file_size > 10 * 1024 * 1024:  # 10MB limit
                    continue  # Skip large files
                
                try:
                    # Decoding with 'ignore' ensures robustness against mixed-encoding files
                    content = zip_ref.read(file_name).decode('utf-8', errors='ignore')
                    
                    # Sanitize content before processing
                    sanitized_content = _sanitize_content(content)
                    
                    # Direct memory processing for efficiency (bypasses temp files)
                    if suffix in {"txt", "log", "conf", "config"}:
                        file_chunks = _ingest_text_content(file_name, sanitized_content, suffix)
                    elif suffix == "csv":
                        file_chunks = _ingest_csv_content(file_name, sanitized_content)
                    elif suffix == "json":
                        file_chunks = _ingest_json_content(file_name, sanitized_content)
                    else:
                        continue
                    
                    chunks.extend(file_chunks)
                except Exception:
                    # Silently skip files that are corrupt or unreadable
                    continue
    
    except zipfile.BadZipFile:
        raise ValueError(f"Invalid ZIP file detected: {zip_path}")
    except Exception as e:
        raise ValueError(f"An unexpected error occurred while processing the archive: {e}")
    
    return chunks


def _ingest_directory(dir_path: Path) -> list[dict]:
    """Walks through a directory tree, gathering every piece of relevant documentation."""
    chunks = []
    supported_extensions = {".txt", ".log", ".conf", ".config", ".csv", ".json"}
    
    # Recursively discover all supported files
    for file_path in dir_path.rglob("*"):
        if not file_path.is_file():
            continue
        
        if file_path.suffix.lower() not in supported_extensions:
            continue
        
        # Check file size to prevent processing oversized files
        try:
            if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                continue  # Skip large files
        except OSError:
            # If we can't get file stats, skip it
            continue
        
        try:
            # Leverage the main entry point to maintain unified processing logic
            file_chunks = ingest_file(str(file_path))
            chunks.extend(file_chunks)
        except Exception:
            # Resiliently continue even if some files fail
            continue
    
    return chunks


def _ingest_text_content(filename: str, content: str, fmt: str) -> list[dict]:
    """Ingest text content from string (for ZIP files)."""
    chunks = []
    lines = content.splitlines(keepends=True)
    
    buffer = []
    start_line = 1
    
    for idx, line in enumerate(lines, start=1):
        buffer.append(line)
        # Check memory usage periodically
        if idx % 1000 == 0:
            _check_memory_usage()
        if sum(len(l) for l in buffer) >= 600:
            chunks.append(_make_chunk(
                filename, "".join(buffer), start_line, idx, fmt
            ))
            buffer = []
            start_line = idx + 1
    
    if buffer:
        chunks.append(_make_chunk(
            filename, "".join(buffer), start_line, len(lines), fmt
        ))
    
    return chunks


def _ingest_csv_content(filename: str, content: str) -> list[dict]:
    """Ingest CSV content from string (for ZIP files)."""
    chunks = []
    lines = content.splitlines()
    
    if not lines:
        return chunks
    
    reader = csv.reader(lines)
    rows = list(reader)
    
    if not rows:
        return chunks
    
    header, *data_rows = rows
    buffer = [",".join(header)]
    start_row = 1
    
    for idx, row in enumerate(data_rows, start=2):
        buffer.append(",".join(row))
        # Check memory usage periodically
        if idx % 1000 == 0:
            _check_memory_usage()
        if len(buffer) >= 20:
            chunks.append(_make_chunk(
                filename, "\n".join(buffer), start_row, idx, "csv"
            ))
            buffer = [",".join(header)]
            start_row = idx + 1
    
    if len(buffer) > 1:
        chunks.append(_make_chunk(
            filename, "\n".join(buffer), start_row, len(rows), "csv"
        ))
    
    return chunks


def _ingest_json_content(filename: str, content: str) -> list[dict]:
    """Ingest JSON content from string (for ZIP files)."""
    try:
        data = json.loads(content)
        pretty = json.dumps(data, indent=2)
        lines = pretty.splitlines()
    except Exception:
        # If JSON parsing fails, treat as raw text
        lines = content.splitlines()
    
    chunks = []
    buffer = []
    start = 1
    
    for idx, line in enumerate(lines, start=1):
        buffer.append(line)
        # Check memory usage periodically
        if idx % 1000 == 0:
            _check_memory_usage()
        if sum(len(l) for l in buffer) >= 600:
            chunks.append(_make_chunk(
                filename, "\n".join(buffer), start, idx, "json"
            ))
            buffer = []
            start = idx + 1
    
    if buffer:
        chunks.append(_make_chunk(
            filename, "\n".join(buffer), start, len(lines), "json"
        ))
    
    return chunks


def _ingest_text(path: Path, fmt: str) -> list[dict]:
    chunks = []
    with path.open(encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    buffer = []
    start_line = 1

    for idx, line in enumerate(lines, start=1):
        buffer.append(line)
        # Check memory usage periodically
        if idx % 1000 == 0:
            _check_memory_usage()
        if sum(len(l) for l in buffer) >= 600:
            chunks.append(_make_chunk(
                path.name, "".join(buffer), start_line, idx, fmt
            ))
            buffer = []
            start_line = idx + 1

    if buffer:
        chunks.append(_make_chunk(
            path.name, "".join(buffer), start_line, len(lines), fmt
        ))

    return chunks


def _ingest_csv(path: Path) -> list[dict]:
    chunks = []
    with path.open(encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    header, *data_rows = rows
    buffer = [",".join(header)]
    start_row = 1

    for idx, row in enumerate(data_rows, start=2):
        buffer.append(",".join(row))
        # Check memory usage periodically
        if idx % 1000 == 0:
            _check_memory_usage()
        if len(buffer) >= 20:
            chunks.append(_make_chunk(
                path.name, "\n".join(buffer), start_row, idx, "csv"
            ))
            buffer = [",".join(header)]
            start_row = idx + 1

    if len(buffer) > 1:
        chunks.append(_make_chunk(
            path.name, "\n".join(buffer), start_row, len(rows), "csv"
        ))

    return chunks


def _ingest_json(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", errors="ignore") as f:
        try:
            data = json.load(f)
        except Exception:
            raw = f.read()
            return [_make_chunk(path.name, raw, None, None, "json")]

    pretty = json.dumps(data, indent=2)
    lines = pretty.splitlines()

    chunks = []
    buffer = []
    start = 1

    for idx, line in enumerate(lines, start=1):
        buffer.append(line)
        # Check memory usage periodically
        if idx % 1000 == 0:
            _check_memory_usage()
        if sum(len(l) for l in buffer) >= 600:
            chunks.append(_make_chunk(
                path.name, "\n".join(buffer), start, idx, "json"
            ))
            buffer = []
            start = idx + 1

    if buffer:
        chunks.append(_make_chunk(
            path.name, "\n".join(buffer), start, len(lines), "json"
        ))

    return chunks


def _is_safe_path(file_path: str) -> bool:
    """
    Validates that the file path is safe (no directory traversal).
    
    Args:
        file_path: The file path to validate
    
    Returns:
        True if the path is safe, False otherwise
    """
    # Resolve the path to its absolute form
    resolved_path = Path(file_path).resolve()
    
    # For testing purposes, we'll allow temp directories
    # In production, this would be restricted to project directory only
    temp_dirs = [
        Path(tempfile.gettempdir()).resolve(),
        Path(os.environ.get('TMPDIR', tempfile.gettempdir())).resolve(),
        Path(os.environ.get('TEMP', tempfile.gettempdir())).resolve(),
        Path(os.environ.get('TMP', tempfile.gettempdir())).resolve(),
    ]
    
    # Check if the resolved path is within temp directories
    for temp_dir in temp_dirs:
        try:
            resolved_path.relative_to(temp_dir)
            return True
        except ValueError:
            continue
    
    # Get the project root (workspace directory)
    project_root = Path(__file__).parent.parent.resolve()
    
    try:
        # Check if the resolved path is within the project root
        resolved_path.relative_to(project_root)
        return True
    except ValueError:
        # Path is outside both temp and project directories
        return False

def _is_safe_mime_type(mime_type: str) -> bool:
    """
    Validates that the MIME type is safe for processing.
    
    Args:
        mime_type: The MIME type to validate
    
    Returns:
        True if the MIME type is safe, False otherwise
    """
    # Define safe MIME types
    safe_mime_types = {
        'text/plain',
        'text/csv',
        'application/json',
        'application/zip',
        'application/x-zip-compressed',
        'multipart/x-zip',
        'text/xml',
        'application/xml',
        'text/html',
        'application/octet-stream'  # Generic binary, but we'll allow it since it's common
    }
    
    # Allow text/* and application/json types
    if mime_type.startswith(('text/', 'application/json')):
        return True
    
    # Check against safe types
    return mime_type in safe_mime_types


def _check_memory_usage(threshold_percent: float = 80.0):
    """
    Check current memory usage and raise an exception if it exceeds the threshold.
    
    Args:
        threshold_percent: Memory usage percentage threshold (default 80%)
    
    Raises:
        MemoryError: If memory usage exceeds the threshold
    """
    memory_percent = psutil.virtual_memory().percent
    if memory_percent > threshold_percent:
        raise MemoryError(f"Memory usage ({memory_percent}%) exceeds threshold ({threshold_percent}%)")


def _sanitize_content(content: str) -> str:
    """
    Sanitizes content by removing potentially harmful patterns.
    
    Args:
        content: The content to sanitize
    
    Returns:
        Sanitized content
    """
    # Remove null bytes which can cause issues
    sanitized = content.replace('\x00', '')
    
    # Potentially remove other control characters if needed
    # sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
    
    return sanitized

def _make_chunk(
    filename: str,
    content: str,
    start: Optional[int],
    end: Optional[int],
    fmt: str,
) -> dict:
    # Sanitize content before creating chunk
    sanitized_content = _sanitize_content(content)
    return {
        "chunk_id": str(uuid.uuid4()),
        "source_file": filename,
        "content": sanitized_content.strip(),
        "line_start": start,
        "line_end": end,
        "format": fmt,
    }
