import json

from app.ingestion.loaders import get_loader
from app.ingestion.service import IngestionService


def test_loader_registry_supports_text_json_and_html(tmp_path):
    text = tmp_path / "note.txt"
    text.write_text("retrieval notes", encoding="utf-8")
    data = tmp_path / "data.json"
    data.write_text(json.dumps({"topic": "rag"}), encoding="utf-8")
    page = tmp_path / "page.html"
    page.write_text("<h1>Title</h1><p>Body</p>", encoding="utf-8")

    assert get_loader(text).load(text)[0].page_content == "retrieval notes"
    assert '"topic": "rag"' in get_loader(data).load(data)[0].page_content
    assert get_loader(page).load(page)[0].page_content == "Title\nBody"


def test_ingestion_preserves_metadata_and_skips_duplicate_content(tmp_path):
    source = tmp_path / "note.md"
    source.write_text("# Retrieval\nCats and documents", encoding="utf-8")
    service = IngestionService()

    first = service.ingest_file(source)
    second = service.ingest_file(source)

    assert first.status == "completed"
    assert first.chunks[0].metadata.source == str(source.resolve())
    assert first.chunks[0].metadata.content_hash == first.content_hash
    assert second.status == "skipped"
    assert second.document_id == first.document_id