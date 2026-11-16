"""Unit Tests for Disk Scheduling Algorithms.

Verifies deterministic head movement calculations against analytical operating systems
benchmarks (Silberschatz) and ensures defensive handling of boundary conditions.
"""

import unittest

from core.disk_scheduling import (
    DISK_ALGORITHMS,
    compare_all_disk,
    run_c_look,
    run_c_scan,
    run_disk_simulation,
    run_fcfs,
    run_look,
    run_scan,
    run_sstf,
)
from core.validators import EmptyInputError, OutOfRangeError


class TestDiskScheduling(unittest.TestCase):

    def setUp(self):
        # Mandatory textbook benchmark dataset
        self.queue = [98, 183, 37, 122, 14, 124, 65, 67]
        self.head = 53
        self.size = 200

    def test_fcfs_benchmark(self):
        res = run_fcfs(self.queue, self.head, self.size, "left")
        self.assertEqual(res.total_movement, 640)
        self.assertEqual(res.sequence[0], 53)
        self.assertEqual(len(res.steps), 8)

    def test_sstf_benchmark(self):
        res = run_sstf(self.queue, self.head, self.size, "left")
        self.assertEqual(res.total_movement, 236)
        # Service order: 65, 67, 37, 14, 98, 122, 124, 183
        self.assertEqual(res.sequence, [53, 65, 67, 37, 14, 98, 122, 124, 183])

    def test_scan_left_benchmark(self):
        res = run_scan(self.queue, self.head, self.size, "left")
        self.assertEqual(res.total_movement, 236)
        self.assertIn(0, res.sequence)  # Touches boundary 0

    def test_look_left_benchmark(self):
        res = run_look(self.queue, self.head, self.size, "left")
        self.assertEqual(res.total_movement, 208)
        self.assertNotIn(0, res.sequence)  # Does NOT touch boundary 0

    def test_c_scan_right_benchmark(self):
        # With return jump counted
        res_counted = run_c_scan(self.queue, self.head, self.size, "right", count_jump=True)
        self.assertEqual(res_counted.total_movement, 382)
        self.assertIsNotNone(res_counted.jump_index)

        # With return jump uncounted
        res_uncounted = run_c_scan(self.queue, self.head, self.size, "right", count_jump=False)
        self.assertEqual(res_uncounted.total_movement, 183)

    def test_c_look_right_benchmark(self):
        # With return jump counted
        res_counted = run_c_look(self.queue, self.head, self.size, "right", count_jump=True)
        self.assertEqual(res_counted.total_movement, 322)
        self.assertIsNotNone(res_counted.jump_index)

        # With return jump uncounted
        res_uncounted = run_c_look(self.queue, self.head, self.size, "right", count_jump=False)
        self.assertEqual(res_uncounted.total_movement, 153)

    def test_compare_all_disk(self):
        comp = compare_all_disk(self.queue, self.head, self.size, "left", count_jump=True)
        self.assertEqual(len(comp["results"]), 6)
        self.assertEqual(comp["results"]["FCFS"]["total_movement"], 640)
        self.assertEqual(comp["results"]["SSTF"]["total_movement"], 236)
        self.assertEqual(comp["results"]["SCAN"]["total_movement"], 236)
        self.assertEqual(comp["results"]["LOOK"]["total_movement"], 208)
        self.assertIn("LOOK", comp["best_algorithms"])

    def test_boundary_single_request(self):
        res = run_disk_simulation([100], 50, 200, "right", "FCFS")
        self.assertEqual(res.total_movement, 50)
        self.assertEqual(res.sequence, [50, 100])

    def test_boundary_request_at_head(self):
        res = run_disk_simulation([50], 50, 200, "right", "FCFS")
        self.assertEqual(res.total_movement, 0)

    def test_boundary_head_at_zero(self):
        res = run_disk_simulation([10, 20, 30], 0, 100, "right", "LOOK")
        self.assertEqual(res.total_movement, 30)

    def test_boundary_all_on_one_side(self):
        res = run_disk_simulation([10, 20, 30], 50, 100, "left", "LOOK")
        self.assertEqual(res.total_movement, 40)

    def test_boundary_duplicate_requests(self):
        res = run_disk_simulation([10, 10, 20], 0, 100, "right", "FCFS")
        self.assertEqual(res.total_movement, 20)


if __name__ == "__main__":
    unittest.main()
