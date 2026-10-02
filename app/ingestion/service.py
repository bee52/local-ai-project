"""Incremental multi-format ingestion service."""

from hashlib import sha256
import logging
import mimetypes
from pathlib import Path
import uuid

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.ingestion.loaders import get_loader
from app.models import DocumentChunk, DocumentMetadata, IngestionResult


logger = logging.getLogger(__name__)


class IngestionService:
    """Load, normalize, split, and incrementally process local documents."""

    def __init__(self, processed_hashes: set[str] | None = None):
        self.processed_hashes = processed_hashes if processed_hashes is not None else set()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    @staticmethod
    def content_hash(path: Path) -> str:
        """Return a stable SHA-256 hash for the source bytes."""
        digest = sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def document_id(path: Path) -> str:
        """Return a stable ID based on the normalized source path."""
        return str(uuid.uuid5(uuid.NAMESPACE_URL, path.resolve().as_uri()))

    def ingest_file(self, path: Path) -> IngestionResult:
        """Ingest one file, skipping content already seen by this service."""
        path = path.expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        content_hash = self.content_hash(path)
        document_id = self.document_id(path)
        if content_hash in self.processed_hashes:
            return IngestionResult(
                source=str(path),
                document_id=document_id,
                content_hash=content_hash,
                status="skipped",
                detail="content hash already indexed",
            )

        documents = get_loader(path).load(path)
        chunks = self._chunks(documents, path, document_id, content_hash)
        self.processed_hashes.add(content_hash)
        logger.info(
            "Document ingested",
            extra={"source": str(path), "chunks": len(chunks)},
        )
        return IngestionResult(
            source=str(path),
            document_id=document_id,
            content_hash=content_hash,
            status="completed",
            chunks=tuple(chunks),
        )

    def load_documents(self, path: Path) -> list[Document]:
        """Load raw documents for legacy callers before chunking or indexing."""
        path = path.expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        return get_loader(path).load(path)

    def ingest_directory(self, directory: Path) -> tuple[IngestionResult, ...]:
        """Ingest supported files in a directory in stable path order."""
        directory = directory.expanduser().resolve()
        if not directory.is_dir():
            raise NotADirectoryError(directory)
        results = []
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix.lower() in self._supported_suffixes():
                results.append(self.ingest_file(path))
        return tuple(results)

    @staticmethod
    def _supported_suffixes() -> set[str]:
        from app.ingestion.loaders import LOADERS

        return set(LOADERS)

    def _chunks(
        self,
        documents: list[Document],
        path: Path,
        document_id: str,
        content_hash: str,
    ) -> list[DocumentChunk]:
        source_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        metadata = DocumentMetadata(
            document_id=document_id,
            source=str(path),
            content_hash=content_hash,
            mime_type=source_type,
            attributes={"filename": path.name},
        )
        chunks: list[DocumentChunk] = []
        for position, document in enumerate(self.text_splitter.split_documents(documents)):
            chunk_id = f"{document_id}:{position}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=document.page_content,
                    metadata=metadata,
                    position=position,
                )
            )
        return chunks
