import unittest

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.chunking import chunk_document
from app.domain import SourceDocument


class ChunkingTests(unittest.TestCase):
    def test_chunk_document_preserves_offsets_and_source(self):
        text = (
            "Refund policy allows returns within thirty days. "
            "Receipts are required for all returns.\n\n"
            "Warranty coverage lasts one year and excludes accidental damage. "
            "Support can approve replacements."
        )
        document = SourceDocument("doc-1", "policy.txt", text)

        chunks = chunk_document(document, max_chars=90, overlap=20, min_chars=20)

        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(chunks[0].source_name, "policy.txt")
        self.assertEqual(text[chunks[0].start_char : chunks[0].end_char].strip(), chunks[0].text)
        self.assertTrue(all(chunk.chunk_id.startswith("doc-1:") for chunk in chunks))

    def test_chunk_document_validates_overlap(self):
        document = SourceDocument("doc-1", "notes.txt", "hello world")

        with self.assertRaises(ValueError):
            chunk_document(document, max_chars=10, overlap=10)


if __name__ == "__main__":
    unittest.main()

