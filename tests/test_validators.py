"""Unit Tests for Defensive Validators and Domain Exceptions.

Validates that bad, out-of-range, or malformed inputs trigger appropriate
domain exceptions carrying field-level diagnostics.
"""

import unittest

from core.validators import (
    EmptyInputError,
    InvalidInputError,
    OutOfRangeError,
    validate_cpu_input,
    validate_deadlock_input,
    validate_disk_input,
    validate_page_input,
    validate_request_input,
)


class TestValidators(unittest.TestCase):

    # 1. Disk Validators
    def test_disk_invalid_size(self):
        with self.assertRaises(OutOfRangeError):
            validate_disk_input([10], 5, 1)  # size < 2
        with self.assertRaises(InvalidInputError):
            validate_disk_input([10], 5, "invalid")

    def test_disk_head_out_of_range(self):
        with self.assertRaises(OutOfRangeError):
            validate_disk_input([10], 250, 200)

    def test_disk_empty_queue(self):
        with self.assertRaises(EmptyInputError):
            validate_disk_input([], 50, 200)

    def test_disk_request_out_of_bounds(self):
        with self.assertRaises(OutOfRangeError):
            validate_disk_input([50, 250], 100, 200)

    # 2. CPU Validators
    def test_cpu_empty_process_list(self):
        with self.assertRaises(EmptyInputError):
            validate_cpu_input([])

    def test_cpu_duplicate_pid(self):
        procs = [
            {"pid": "P1", "arrival": 0, "burst": 5},
            {"pid": "P1", "arrival": 1, "burst": 2},
        ]
        with self.assertRaises(InvalidInputError):
            validate_cpu_input(procs)

    def test_cpu_negative_burst(self):
        procs = [{"pid": "P1", "arrival": 0, "burst": -5}]
        with self.assertRaises(OutOfRangeError):
            validate_cpu_input(procs)

    def test_cpu_negative_quantum(self):
        procs = [{"pid": "P1", "arrival": 0, "burst": 5}]
        with self.assertRaises(OutOfRangeError):
            validate_cpu_input(procs, quantum=-2)

    # 3. Page Validators
    def test_pages_empty_reference(self):
        with self.assertRaises(EmptyInputError):
            validate_page_input([], 3)

    def test_pages_invalid_frames(self):
        with self.assertRaises(OutOfRangeError):
            validate_page_input([1, 2, 3], 0)

    def test_pages_negative_page(self):
        with self.assertRaises(OutOfRangeError):
            validate_page_input([1, -5, 2], 3)

    # 4. Deadlock Validators
    def test_deadlock_mismatched_dimensions(self):
        avail = [3, 3, 2]
        alloc = {"P0": [1, 2]}  # Only 2 resources instead of 3
        max_m = {"P0": [1, 2, 3]}
        with self.assertRaises(InvalidInputError):
            validate_deadlock_input(avail, alloc, max_m)

    def test_deadlock_alloc_exceeds_max(self):
        avail = [3, 3, 2]
        alloc = {"P0": [5, 2, 2]}
        max_m = {"P0": [3, 2, 2]}  # 5 > 3
        with self.assertRaises(OutOfRangeError):
            validate_deadlock_input(avail, alloc, max_m)


if __name__ == "__main__":
    unittest.main()
