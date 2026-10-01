"""Small exact cases check validity, weights, cutoff semantics, and time fallback."""
import itertools
import time
import unittest
from dataclasses import replace
from types import MappingProxyType

from adapters.mine import MySolver
from data import Instance, compute_digest, effective_table
from validator import validate


def instance(points, weights, sites, k, radius=20, penalty=100):
    item = Instance(name='small-check', profile=MappingProxyType({'family': 'test', 'shifted': False}),
                    size=len(points), digest='', points=tuple(points), weights=tuple(weights),
                    sites=tuple(sites), k=k, radius=radius, penalty=penalty)
    # The provided distance table caches by digest; synthetic fixtures need one too.
    return replace(item, digest=compute_digest(item))


class SolverTests(unittest.TestCase):
    def solve_and_check(self, item, seconds=0.6):
        started = time.perf_counter()
        candidates = []
        def submit(plan):
            cost, reason = validate(item, plan)
            self.assertIsNone(reason)
            candidates.append(cost)
            elapsed = time.perf_counter() - started
            return {'accepted': True, 'reason': None, 'cost': cost, 'best': min(candidates),
                    'elapsed_s': elapsed, 'remaining_s': seconds - elapsed}
        plan = MySolver().solve(item, submit)
        cost, reason = validate(item, plan)
        self.assertIsNone(reason)
        self.assertEqual(len(plan['sites']), item.k)
        self.assertEqual(len(set(plan['sites'])), item.k)
        self.assertEqual(candidates, sorted(candidates, reverse=True))
        self.assertEqual(cost, min(candidates))
        return plan, cost

    def test_population_weights_and_two_monitors_against_exact_optimum(self):
        item = instance([(0, 0), (10, 0), (10, 10), (100, 100)], [1, 100, 10, 1],
                        [(0, 0), (10, 0), (10, 10), (100, 100), (50, 50)], 2)
        _, cost = self.solve_and_check(item)
        exact = min(validate(item, {'sites': list(s)})[0]
                    for s in itertools.combinations(range(len(item.sites)), item.k))
        self.assertEqual(cost, exact)

    def test_integer_distance_and_cutoff(self):
        item = instance([(3, 5), (0, 6)], [2, 3], [(0, 0), (0, 6)], 1, radius=5, penalty=20)
        self.assertEqual(effective_table(item), [[5, 3], [20, 0]])
        plan, cost = self.solve_and_check(item)
        self.assertEqual(plan['sites'], [1])
        self.assertEqual(cost, 6)

    def test_all_uncovered_ties_keep_valid_plan(self):
        item = instance([(100, 100)], [5], [(0, 0), (1, 1), (2, 2)], 2, radius=2, penalty=50)
        _, cost = self.solve_and_check(item)
        self.assertEqual(cost, 250)

    def test_all_candidates_selected(self):
        item = instance([(0, 0)], [10], [(0, 0), (10, 0)], 2)
        plan, cost = self.solve_and_check(item)
        self.assertEqual(plan['sites'], [0, 1])
        self.assertEqual(cost, 0)

    def test_no_remaining_time_returns_initial_valid_plan(self):
        item = instance([(0, 0)], [10], [(10, 0), (0, 0)], 1)
        plan, cost = self.solve_and_check(item, seconds=-1)
        self.assertEqual(plan['sites'], [0])
        self.assertEqual(cost, 100)


if __name__ == '__main__':
    unittest.main()
