import json
import csv
import uuid
from pathlib import Path


def ingest_file(file_path: str) -> list[dict]:
    path = Path(file_path)
    suffix = path.suffix.lower().lstrip(".")

    if suffix not in {"txt", "log", "csv", "json"}:
        raise ValueError(f"Unsupported file type: {suffix}")

    if suffix in {"txt", "log"}:
        return _ingest_text(path, suffix)
    if suffix == "csv":
        return _ingest_csv(path)
    if suffix == "json":
        return _ingest_json(path)


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
    start: int | None,
    end: int | None,
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
