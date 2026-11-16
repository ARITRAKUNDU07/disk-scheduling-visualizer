"""Unit Tests for CPU Scheduling Algorithms.

Verifies FCFS, SJF, SRTF, Round Robin, and Priority scheduling algorithms against
mandatory benchmark metrics and tests defensive scheduling boundaries.
"""

import unittest

from core.cpu_scheduling import (
    CPU_ALGORITHMS,
    compare_all_cpu,
    run_cpu_simulation,
    run_fcfs_cpu,
    run_priority_cpu,
    run_round_robin_cpu,
    run_sjf_cpu,
    run_srtf_cpu,
)


class TestCPUScheduling(unittest.TestCase):

    def setUp(self):
        # Mandatory textbook benchmark processes: P1(0, 24), P2(0, 3), P3(0, 3)
        self.procs = [
            {"pid": "P1", "arrival": 0, "burst": 24, "priority": 3},
            {"pid": "P2", "arrival": 0, "burst": 3, "priority": 1},
            {"pid": "P3", "arrival": 0, "burst": 3, "priority": 2},
        ]

    def test_fcfs_benchmark(self):
        res = run_fcfs_cpu(self.procs)
        self.assertEqual(res.avg_waiting, 17.0)
        self.assertEqual(res.avg_turnaround, 27.0)
        self.assertEqual(len(res.gantt), 3)

    def test_sjf_non_preemptive_benchmark(self):
        res = run_sjf_cpu(self.procs)
        self.assertEqual(res.avg_waiting, 3.0)
        self.assertEqual(res.avg_turnaround, 13.0)
        # Execution order should be P2, P3, P1
        self.assertEqual([seg.pid for seg in res.gantt], ["P2", "P3", "P1"])

    def test_round_robin_benchmark(self):
        res = run_round_robin_cpu(self.procs, quantum=4.0)
        self.assertEqual(res.avg_waiting, 5.67)
        self.assertEqual(res.avg_turnaround, 15.67)

    def test_srtf_preemptive(self):
        procs = [
            {"pid": "P1", "arrival": 0, "burst": 8, "priority": 1},
            {"pid": "P2", "arrival": 1, "burst": 4, "priority": 1},
            {"pid": "P3", "arrival": 2, "burst": 9, "priority": 1},
            {"pid": "P4", "arrival": 3, "burst": 5, "priority": 1},
        ]
        res = run_srtf_cpu(procs)
        self.assertLess(res.avg_waiting, 10.0)
        self.assertTrue(len(res.gantt) >= 4)

    def test_priority_non_preemptive(self):
        res = run_priority_cpu(self.procs)
        # P2 (priority 1), P3 (priority 2), P1 (priority 3)
        self.assertEqual([seg.pid for seg in res.gantt], ["P2", "P3", "P1"])

    def test_boundary_single_process(self):
        procs = [{"pid": "P1", "arrival": 0, "burst": 10, "priority": 1}]
        res = run_cpu_simulation(procs, "FCFS")
        self.assertEqual(res.avg_waiting, 0.0)
        self.assertEqual(res.avg_turnaround, 10.0)

    def test_boundary_quantum_larger_than_bursts(self):
        res = run_round_robin_cpu(self.procs, quantum=100.0)
        # Should degenerate to FCFS behavior
        self.assertEqual(res.avg_waiting, 17.0)

    def test_compare_all_cpu(self):
        comp = compare_all_cpu(self.procs, quantum=4.0)
        self.assertEqual(len(comp["results"]), 5)
        self.assertEqual(comp["results"]["FCFS"]["avg_waiting"], 17.0)
        self.assertEqual(comp["results"]["SJF"]["avg_waiting"], 3.0)
        self.assertEqual(comp["results"]["Round Robin"]["avg_waiting"], 5.67)
        self.assertIn("SJF", comp["best_algorithms"])


if __name__ == "__main__":
    unittest.main()
