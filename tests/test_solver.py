"""Small exact cases check validity, weights, cutoff semantics, and time fallback."""
import itertools
import random
import time
import unittest
from dataclasses import replace
from types import MappingProxyType

from adapters.mine import MySolver, _best_swap
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

    def test_sparse_exchange_matches_every_brute_force_neighbor(self):
        # Independently validate every exchange, including ties, zero weights,
        # uncovered points and replacements covering a removed site's demand.
        rng = random.Random(728)
        for trial in range(40):
            item = instance(
                [(rng.randrange(9), rng.randrange(9)) for _ in range(7)],
                [rng.randrange(6) for _ in range(7)],
                [(rng.randrange(9), rng.randrange(9)) for _ in range(6)],
                1 + trial % 4, radius=3, penalty=15)
            table = effective_table(item)
            benefits = [[] for _ in item.sites]
            for point, (weight, row) in enumerate(zip(item.weights, table)):
                for site, distance in enumerate(row):
                    value = weight * (item.penalty - distance)
                    if value > 0:
                        benefits[site].append((point, value))
            opened = rng.sample(range(len(item.sites)), item.k)
            near, second, owner = [], [], []
            for weight, row in zip(item.weights, table):
                ranked = sorted(
                    ((weight * (item.penalty - row[site]), pos)
                     for pos, site in enumerate(opened)),
                    key=lambda value: (-value[0], value[1]))
                near.append(ranked[0][0])
                second.append(ranked[1][0] if item.k > 1 else 0)
                owner.append(ranked[0][1])
            before = validate(item, {'sites': opened})[0]
            best_cost = before
            for pos in range(item.k):
                for site in range(len(item.sites)):
                    if site not in opened:
                        neighbor = list(opened)
                        neighbor[pos] = site
                        best_cost = min(best_cost, validate(item, {'sites': neighbor})[0])
            delta, swap = _best_swap(
                benefits, opened, near, second, owner, float('inf'))
            with self.subTest(trial=trial):
                self.assertEqual(before + delta, best_cost)
                if swap is None:
                    self.assertEqual(best_cost, before)
                else:
                    pos, site = swap
                    neighbor = list(opened)
                    neighbor[pos] = site
                    self.assertEqual(validate(item, {'sites': neighbor})[0], best_cost)


if __name__ == '__main__':
    unittest.main()
