"""Unit Tests for Virtual Memory Page Replacement Algorithms.

Verifies FIFO, LRU, and Optimal page fault counts against analytical benchmarks
and validates empirical demonstration of Belady's Anomaly.
"""

import unittest

from core.page_replacement import (
    compare_all_pages,
    demonstrate_belady,
    run_fifo_pages,
    run_lru_pages,
    run_optimal_pages,
    run_page_simulation,
)


class TestPageReplacement(unittest.TestCase):

    def setUp(self):
        # Mandatory textbook reference string with 3 frames
        self.reference = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
        self.frames = 3

    def test_fifo_benchmark(self):
        res = run_fifo_pages(self.reference, self.frames)
        self.assertEqual(res.total_faults, 15)
        self.assertEqual(res.total_hits, 5)
        self.assertEqual(len(res.steps), 20)

    def test_lru_benchmark(self):
        res = run_lru_pages(self.reference, self.frames)
        self.assertEqual(res.total_faults, 12)
        self.assertEqual(res.total_hits, 8)

    def test_optimal_benchmark(self):
        res = run_optimal_pages(self.reference, self.frames)
        self.assertEqual(res.total_faults, 9)
        self.assertEqual(res.total_hits, 11)

    def test_belady_anomaly(self):
        bel = demonstrate_belady()
        self.assertEqual(bel["faults_3_frames"], 9)
        self.assertEqual(bel["faults_4_frames"], 10)
        self.assertTrue(bel["is_anomaly_demonstrated"])

    def test_compare_all_pages(self):
        comp = compare_all_pages(self.reference, self.frames)
        self.assertEqual(comp["results"]["FIFO"]["total_faults"], 15)
        self.assertEqual(comp["results"]["LRU"]["total_faults"], 12)
        self.assertEqual(comp["results"]["Optimal"]["total_faults"], 9)
        self.assertIn("Optimal", comp["best_algorithms"])

    def test_boundary_single_frame(self):
        ref = [1, 2, 1, 3]
        res = run_page_simulation(ref, 1, "FIFO")
        self.assertEqual(res.total_faults, 4)

    def test_boundary_all_hits_after_loading(self):
        ref = [1, 2, 1, 2, 1, 2]
        res = run_page_simulation(ref, 2, "LRU")
        self.assertEqual(res.total_faults, 2)
        self.assertEqual(res.total_hits, 4)

    def test_boundary_frames_larger_than_unique_pages(self):
        ref = [1, 2, 3, 2, 1]
        res = run_page_simulation(ref, 10, "Optimal")
        self.assertEqual(res.total_faults, 3)
        self.assertEqual(res.total_hits, 2)


if __name__ == "__main__":
    unittest.main()
