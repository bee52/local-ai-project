from app.models import DocumentChunk, DocumentMetadata


def make_chunk(chunk_id: str, text: str) -> DocumentChunk:
    metadata = DocumentMetadata(
        document_id="doc-1",
        source="fixture.md",
        content_hash="hash-1",
        mime_type="text/markdown",
        attributes={"page": 1},
    )
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id="doc-1",
        text=text,
        metadata=metadata,
        position=0,
    )