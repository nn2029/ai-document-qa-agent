import unittest

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.citations import build_citations
from app.domain import DocumentChunk, RetrievalHit


class CitationTests(unittest.TestCase):
    def test_build_citations_keeps_source_provenance(self):
        chunk = DocumentChunk(
            "doc:0001",
            "doc",
            "handbook.txt",
            "Employees may work remotely two days per week. Managers approve exceptions.",
            100,
            173,
            1,
        )
        hit = RetrievalHit(chunk=chunk, score=2.4, matched_terms=("remote", "week"))

        citations = build_citations([hit])

        self.assertEqual(citations[0].citation_id, "[1]")
        self.assertEqual(citations[0].source_name, "handbook.txt")
        self.assertEqual(citations[0].chunk_id, "doc:0001")
        self.assertGreaterEqual(citations[0].start_char, 100)
        self.assertIn("remotely", citations[0].quote)


if __name__ == "__main__":
    unittest.main()

