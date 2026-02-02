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
    """
    path = Path(file_path)
    
    # Delegate to specialized handlers based on source type
    if path.suffix.lower() == ".zip":
        return _ingest_zip(path)
    
    if path.is_dir():
        return _ingest_directory(path)
    
    # Process individual files based on their digital format
    suffix = path.suffix.lower().lstrip(".")
    
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
                
                try:
                    # Decoding with 'ignore' ensures robustness against mixed-encoding files
                    content = zip_ref.read(file_name).decode('utf-8', errors='ignore')
                    
                    # Direct memory processing for efficiency (bypasses temp files)
                    if suffix in {"txt", "log", "conf", "config"}:
                        file_chunks = _ingest_text_content(file_name, content, suffix)
                    elif suffix == "csv":
                        file_chunks = _ingest_csv_content(file_name, content)
                    elif suffix == "json":
                        file_chunks = _ingest_json_content(file_name, content)
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


def _make_chunk(
    filename: str,
    content: str,
    start: Optional[int],
    end: Optional[int],
    fmt: str,
) -> dict:
    return {
        "chunk_id": str(uuid.uuid4()),
        "source_file": filename,
        "content": content.strip(),
        "line_start": start,
        "line_end": end,
        "format": fmt,
    }
