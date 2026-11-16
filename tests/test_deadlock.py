"""Unit Tests for Banker's Deadlock Avoidance Algorithm.

Verifies system safety state determination, safe sequence construction,
and dynamic resource request arbitration with rollback guarantees.
"""

import unittest

from core.deadlock import evaluate_resource_request, evaluate_safety
from core.validators import OutOfRangeError


class TestDeadlock(unittest.TestCase):

    def setUp(self):
        # Mandatory textbook benchmark data (5 processes, 3 resource types)
        self.available = [3, 3, 2]
        self.allocation = {
            "P0": [0, 1, 0],
            "P1": [2, 0, 0],
            "P2": [3, 0, 2],
            "P3": [2, 1, 1],
            "P4": [0, 0, 2],
        }
        self.max = {
            "P0": [7, 5, 3],
            "P1": [3, 2, 2],
            "P2": [9, 0, 2],
            "P3": [2, 2, 2],
            "P4": [4, 3, 3],
        }

    def test_banker_safety_benchmark(self):
        res = evaluate_safety(self.available, self.allocation, self.max)
        self.assertTrue(res.is_safe)
        self.assertEqual(res.safe_sequence, ["P1", "P3", "P4", "P0", "P2"])
        self.assertEqual(len(res.steps), 5)

    def test_banker_p1_request_granted(self):
        # P1 requests [1, 0, 2]
        res = evaluate_resource_request(
            self.available, self.allocation, self.max, "P1", [1, 0, 2]
        )
        self.assertTrue(res.granted)
        self.assertIn("GRANTED", res.reason)
        self.assertIsNotNone(res.safety_after_allocation)
        self.assertTrue(res.safety_after_allocation.is_safe)

    def test_banker_p0_request_granted(self):
        # P0 requests [0, 2, 0]
        res = evaluate_resource_request(
            self.available, self.allocation, self.max, "P0", [0, 2, 0]
        )
        self.assertTrue(res.granted)
        self.assertIn("GRANTED", res.reason)

    def test_banker_request_exceeds_available(self):
        # P4 requests [3, 3, 0] when available is [3, 3, 2], but P4 max is [4,3,3], alloc [0,0,2], need [4,3,1]
        # P0 requests [0, 4, 0] when available is [3, 3, 2] (3 < 4)
        res = evaluate_resource_request(
            self.available, self.allocation, self.max, "P0", [0, 4, 0]
        )
        self.assertFalse(res.granted)
        self.assertIn("WAIT REQUIRED", res.reason)

    def test_banker_request_exceeds_need(self):
        # P1 need is [1, 2, 2]. Request [2, 0, 0] exceeds need!
        with self.assertRaises(OutOfRangeError):
            evaluate_resource_request(
                self.available, self.allocation, self.max, "P1", [2, 0, 0]
            )

    def test_banker_unsafe_state_detection(self):
        # Modify available to [0, 0, 0] so no process can finish
        res = evaluate_safety([0, 0, 0], self.allocation, self.max)
        self.assertFalse(res.is_safe)
        self.assertEqual(res.safe_sequence, [])
        self.assertIn("UNSAFE", res.reason)


if __name__ == "__main__":
    unittest.main()
