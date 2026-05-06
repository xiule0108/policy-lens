from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.services.document_parser import ParsedBlock


def estimate_token_count(text: str) -> int:
    return max(1, len(text) // 2)


def split_text(text: str, max_chars: int) -> list[str]:
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than 0.")
    clean_text = text.strip()
    if not clean_text:
        return []
    if len(clean_text) <= max_chars:
        return [clean_text]

    parts: list[str] = []
    remaining = clean_text
    while len(remaining) > max_chars:
        cut_at = remaining.rfind("\n", 0, max_chars + 1)
        if cut_at <= 0:
            cut_at = remaining.rfind(" ", 0, max_chars + 1)
        if cut_at <= 0:
            cut_at = max_chars
        part = remaining[:cut_at].strip()
        if not part:
            part = remaining[:max_chars].strip()
            cut_at = max_chars
        if part:
            parts.append(part)
        remaining = remaining[cut_at:].strip()
    if remaining:
        parts.append(remaining)
    return parts


def build_document_chunks(
    *,
    document_id: str,
    project_id: str,
    blocks: Iterable[ParsedBlock],
    max_chars: int = 2000,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for block_index, block in enumerate(blocks):
        for part_index, content in enumerate(split_text(block.text, max_chars=max_chars)):
            metadata = {
                **(block.metadata or {}),
                "source_block_index": block_index,
            }
            if part_index:
                metadata["split_part_index"] = part_index
            chunks.append(
                {
                    "document_id": document_id,
                    "project_id": project_id,
                    "chunk_index": len(chunks),
                    "page_start": block.page_start,
                    "page_end": block.page_end,
                    "section_title": block.section_title,
                    "content": content,
                    "content_type": block.content_type,
                    "token_count": estimate_token_count(content),
                    "metadata": metadata,
                }
            )
    return chunks
