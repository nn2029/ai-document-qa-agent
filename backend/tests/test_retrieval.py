import unittest

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain import DocumentChunk
from app.retrieval import retrieve, tokenize


class RetrievalTests(unittest.TestCase):
    def test_tokenize_removes_common_stop_words(self):
        self.assertEqual(tokenize("What is the refund policy?"), ["refund", "policy"])

    def test_retrieve_ranks_relevant_chunks_first(self):
        chunks = [
            DocumentChunk("doc:0001", "doc", "policy.txt", "The store policy mentions lunch menus.", 0, 39, 1),
            DocumentChunk(
                "doc:0002",
                "doc",
                "policy.txt",
                "The refund policy allows returns within thirty days with a receipt.",
                32,
                96,
                2,
            ),
        ]

        hits = retrieve("What does the refund policy allow?", chunks, top_k=2)

        self.assertEqual(hits[0].chunk.chunk_id, "doc:0002")
        self.assertIn("refund", hits[0].matched_terms)
        self.assertGreater(hits[0].score, hits[-1].score)


if __name__ == "__main__":
    unittest.main()
