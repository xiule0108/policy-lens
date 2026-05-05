from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import unicodedata

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
    original_filename: str
    file_name: str
    file_type: str
    content_type: str
    file_size: int
    sha256: str


def extract_original_filename(filename: str | None) -> str:
    raw_filename = (filename or "").replace("\\", "/").split("/")[-1]
    raw_filename = unicodedata.normalize("NFKC", raw_filename)
    raw_filename = "".join(char for char in raw_filename if ord(char) >= 32 and ord(char) != 127)
    raw_filename = raw_filename.strip()
    if raw_filename in {"", ".", ".."}:
        return "upload.bin"
    return raw_filename


def truncate_filename(stem: str, suffix: str) -> str:
    max_stem_length = max(1, MAX_FILENAME_LENGTH - len(suffix))
    if len(stem) > max_stem_length:
        stem = stem[:max_stem_length].rstrip(" ._")
    if not stem:
        stem = "upload"
    return f"{stem}{suffix}" if suffix else stem


def normalize_filename(filename: str | None) -> str:
    original_filename = extract_original_filename(filename)
    suffix = Path(original_filename).suffix
    stem = original_filename[: -len(suffix)] if suffix else original_filename

    stem = re.sub(r"(?u)[^\w .-]+", "_", stem)
    stem = re.sub(r"\s+", "_", stem).strip(" ._")
    if not stem:
        stem = "upload"

    suffix = re.sub(r"[^A-Za-z0-9.]+", "", suffix)
    if suffix == ".":
        suffix = ""

    return truncate_filename(stem, suffix)


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
    original_filename = extract_original_filename(upload_file.filename)
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
        original_filename=original_filename,
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
