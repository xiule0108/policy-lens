import pytest

from app.services.chunking_service import build_document_chunks, estimate_token_count, split_text
from app.services.document_parser import ParsedBlock


def test_estimate_token_count_returns_at_least_one() -> None:
    assert estimate_token_count("") == 1
    assert estimate_token_count("abcd") == 2


def test_short_text_generates_one_chunk_with_block_metadata() -> None:
    block = ParsedBlock(
        text="Policy impact paragraph",
        content_type="paragraph",
        page_start=2,
        page_end=2,
        section_title="Impact",
        metadata={"source": "unit"},
    )

    chunks = build_document_chunks(
        document_id="document-1",
        project_id="project-1",
        blocks=[block],
        max_chars=2000,
    )

    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["page_start"] == 2
    assert chunks[0]["page_end"] == 2
    assert chunks[0]["section_title"] == "Impact"
    assert chunks[0]["content"] == "Policy impact paragraph"
    assert chunks[0]["content_type"] == "paragraph"
    assert chunks[0]["token_count"] == estimate_token_count("Policy impact paragraph")
    assert chunks[0]["metadata"]["source"] == "unit"


def test_long_text_is_split_with_continuous_indexes() -> None:
    block = ParsedBlock(text=("alpha " * 20).strip(), content_type="paragraph")

    chunks = build_document_chunks(
        document_id="document-1",
        project_id="project-1",
        blocks=[block],
        max_chars=30,
    )

    assert len(chunks) > 1
    assert [chunk["chunk_index"] for chunk in chunks] == list(range(len(chunks)))
    assert all(len(chunk["content"]) <= 30 for chunk in chunks)
    assert "".join(chunk["content"].replace(" ", "") for chunk in chunks) == block.text.replace(" ", "")


def test_empty_blocks_are_filtered() -> None:
    chunks = build_document_chunks(
        document_id="document-1",
        project_id="project-1",
        blocks=[
            ParsedBlock(text="  ", content_type="paragraph"),
            ParsedBlock(text="Useful text", content_type="paragraph"),
        ],
        max_chars=2000,
    )

    assert len(chunks) == 1
    assert chunks[0]["content"] == "Useful text"


def test_split_text_rejects_non_positive_max_chars() -> None:
    with pytest.raises(ValueError, match="max_chars must be greater than 0"):
        split_text("hello", max_chars=0)


def test_build_document_chunks_rejects_non_positive_max_chars() -> None:
    with pytest.raises(ValueError, match="max_chars must be greater than 0"):
        build_document_chunks(
            document_id="document-1",
            project_id="project-1",
            blocks=[ParsedBlock(text="hello", content_type="paragraph")],
            max_chars=0,
        )
