import unittest

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain import DocumentChunk, SourceDocument
from app.store import DocumentStore


def make_document(document_id: str, text: str) -> SourceDocument:
    return SourceDocument(document_id=document_id, filename=f"{document_id}.txt", text=text)


def make_chunk(document_id: str, ordinal: int, text: str) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=f"{document_id}:{ordinal:04d}",
        document_id=document_id,
        source_name=f"{document_id}.txt",
        text=text,
        start_char=0,
        end_char=len(text),
        ordinal=ordinal,
    )


class DocumentStoreTests(unittest.TestCase):
    def test_store_prunes_oldest_document_when_limit_is_reached(self):
        store = DocumentStore(max_documents=2, max_chunks=10)

        store.add_document(make_document("doc1", "refund policy"), [make_chunk("doc1", 1, "refund policy")])
        store.add_document(make_document("doc2", "shipping policy"), [make_chunk("doc2", 1, "shipping policy")])
        store.add_document(make_document("doc3", "warranty policy"), [make_chunk("doc3", 1, "warranty policy")])

        self.assertEqual(
            [document["document_id"] for document in store.list_documents()],
            ["doc2", "doc3"],
        )
        self.assertEqual(store.stats().document_count, 2)

    def test_search_uses_index_after_replacement(self):
        store = DocumentStore(max_documents=5, max_chunks=10)
        store.add_document(make_document("doc", "refund policy"), [make_chunk("doc", 1, "refund policy")])
        store.add_document(make_document("doc", "shipping windows"), [make_chunk("doc", 1, "shipping windows")])

        hits = store.search("refund", top_k=3)

        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
