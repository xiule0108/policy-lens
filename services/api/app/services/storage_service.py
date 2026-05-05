from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re

from fastapi import UploadFile


CHUNK_SIZE = 1024 * 1024
MAX_FILENAME_LENGTH = 180


class StorageError(Exception):
    """Base class for local storage failures."""


class EmptyUploadError(StorageError):
    """Raised when an uploaded file has no content."""


class UploadExtensionError(StorageError):
    """Raised when an uploaded file extension is not allowed."""


class UploadTooLargeError(StorageError):
    """Raised when an uploaded file exceeds the configured size limit."""


class StoragePathError(StorageError):
    """Raised when a storage key cannot be resolved safely."""


@dataclass(frozen=True)
class StoredFile:
    storage_key: str
    absolute_path: Path
    file_name: str
    file_type: str
    content_type: str
    file_size: int
    sha256: str


def normalize_filename(filename: str | None) -> str:
    raw_filename = (filename or "").replace("\\", "/").split("/")[-1]
    raw_filename = "".join(char for char in raw_filename if ord(char) >= 32 and ord(char) != 127)
    raw_filename = raw_filename.strip()
    if raw_filename in {"", ".", ".."}:
        return "upload.bin"

    safe_filename = re.sub(r"[^A-Za-z0-9._ -]+", "_", raw_filename)
    safe_filename = re.sub(r"\s+", "_", safe_filename).strip("._ ")
    if not safe_filename:
        return "upload.bin"

    if len(safe_filename) <= MAX_FILENAME_LENGTH:
        return safe_filename

    suffix = Path(safe_filename).suffix
    stem = safe_filename[: MAX_FILENAME_LENGTH - len(suffix)]
    return f"{stem.rstrip('._ ')}{suffix}" if suffix else safe_filename[:MAX_FILENAME_LENGTH]


def normalize_allowed_extensions(allowed_extensions: set[str]) -> set[str]:
    return {
        extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        for extension in allowed_extensions
        if extension
    }


def validate_upload_extension(filename: str, allowed_extensions: set[str]) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in normalize_allowed_extensions(allowed_extensions):
        raise UploadExtensionError(f"Unsupported upload extension: {extension or '<none>'}")
    return extension


def cleanup_empty_dirs(path: Path, storage_root: Path) -> None:
    current = path
    while current != storage_root and current.exists():
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def delete_path_and_empty_parents(path: Path, storage_root: Path) -> None:
    if path.exists():
        path.unlink()
    cleanup_empty_dirs(path.parent, storage_root)


def ensure_child_path(storage_root: Path, path: Path) -> Path:
    resolved_root = storage_root.resolve()
    resolved_path = path.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise StoragePathError("Storage path escapes the configured storage root.") from exc
    return resolved_path


def save_upload_file(
    *,
    upload_file: UploadFile,
    storage_root: Path,
    project_id: str,
    document_id: str,
    max_size_bytes: int,
    allowed_extensions: set[str],
) -> StoredFile:
    safe_filename = normalize_filename(upload_file.filename)
    file_type = validate_upload_extension(safe_filename, allowed_extensions)
    storage_root = storage_root.resolve()
    target_dir = storage_root / "documents" / project_id / document_id
    target_path = ensure_child_path(storage_root, target_dir / safe_filename)
    temp_path = target_path.with_name(f".{target_path.name}.tmp")

    target_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    file_size = 0

    try:
        with temp_path.open("wb") as output:
            while True:
                chunk = upload_file.file.read(CHUNK_SIZE)
                if not chunk:
                    break
                next_size = file_size + len(chunk)
                if next_size > max_size_bytes:
                    raise UploadTooLargeError("Uploaded file exceeds the configured size limit.")
                output.write(chunk)
                digest.update(chunk)
                file_size = next_size

        if file_size == 0:
            raise EmptyUploadError("Uploaded file is empty.")

        temp_path.replace(target_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        if target_path.exists():
            target_path.unlink()
        cleanup_empty_dirs(target_dir, storage_root)
        raise

    storage_key = f"documents/{project_id}/{document_id}/{safe_filename}"
    return StoredFile(
        storage_key=storage_key,
        absolute_path=target_path,
        file_name=safe_filename,
        file_type=file_type,
        content_type=upload_file.content_type or "application/octet-stream",
        file_size=file_size,
        sha256=digest.hexdigest(),
    )


def resolve_storage_path(storage_root: Path, storage_key: str) -> Path:
    clean_key = storage_key.replace("\\", "/").lstrip("/")
    return ensure_child_path(storage_root.resolve(), storage_root / clean_key)


def delete_stored_file(absolute_path: Path, storage_root: Path) -> None:
    delete_path_and_empty_parents(absolute_path, storage_root.resolve())
