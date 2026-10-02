"""Format-specific document loaders with a common normalized output."""

import csv
import importlib
import json
from abc import ABC, abstractmethod
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader


class _HTMLTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)

    def text(self) -> str:
        return "\n".join(self.parts)


class DocumentLoader(ABC):
    """Load one source into LangChain documents while preserving source metadata."""

    @abstractmethod
    def load(self, path: Path) -> list[Document]:
        raise NotImplementedError


class TextLoader(DocumentLoader):
    def load(self, path: Path) -> list[Document]:
        return [Document(page_content=path.read_text(encoding="utf-8"))]


class HTMLDocumentLoader(DocumentLoader):
    def load(self, path: Path) -> list[Document]:
        parser = _HTMLTextParser()
        parser.feed(path.read_text(encoding="utf-8"))
        return [Document(page_content=parser.text())]


class JSONDocumentLoader(DocumentLoader):
    def load(self, path: Path) -> list[Document]:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
        return [Document(page_content=json.dumps(value, ensure_ascii=True, indent=2))]


class CSVDocumentLoader(DocumentLoader):
    def load(self, path: Path) -> list[Document]:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        content = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows)
        return [Document(page_content=content)]


class PDFDocumentLoader(DocumentLoader):
    def load(self, path: Path) -> list[Document]:
        return PyPDFLoader(str(path)).load()


class DOCXDocumentLoader(DocumentLoader):
    def load(self, path: Path) -> list[Document]:
        try:
            docx_module = importlib.import_module("docx")
        except ImportError as exc:
            raise RuntimeError(
                "DOCX ingestion requires the optional python-docx package"
            ) from exc
        document = docx_module.Document(str(path))
        content = "\n".join(paragraph.text for paragraph in document.paragraphs)
        return [Document(page_content=content)]


LOADERS: dict[str, DocumentLoader] = {
    ".csv": CSVDocumentLoader(),
    ".docx": DOCXDocumentLoader(),
    ".htm": HTMLDocumentLoader(),
    ".html": HTMLDocumentLoader(),
    ".json": JSONDocumentLoader(),
    ".md": TextLoader(),
    ".pdf": PDFDocumentLoader(),
    ".text": TextLoader(),
    ".txt": TextLoader(),
}


def get_loader(path: Path) -> DocumentLoader:
    """Return the loader registered for a source extension."""
    try:
        return LOADERS[path.suffix.lower()]
    except KeyError as exc:
        supported = ", ".join(sorted(LOADERS))
        raise ValueError(
            f"Unsupported document type '{path.suffix or '<none>'}'. "
            f"Supported types: {supported}"
        ) from exc
