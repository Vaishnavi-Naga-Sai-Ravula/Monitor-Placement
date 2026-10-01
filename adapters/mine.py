"""Sparse greedy construction, cached swap descent, and perturbed restarts.

Only valid site selections are submitted. There are no third-party dependencies,
instance-name checks, reference-cost lookups, or changes to the evaluator.
"""
import random
import time

from adapter import Solver, dist_table

SAFETY_SECONDS = 0.20


def _best_swap(benefits, opened, near, second, owner, deadline):
    """Find the best exchange using only nonzero population-weighted savings."""
    k = len(opened)
    selected = set(opened)
    removal_loss = [0] * k
    for first, runner_up, pos in zip(near, second, owner):
        removal_loss[pos] += first - runner_up

    best_delta, best_swap = 0, None
    for site, covered in enumerate(benefits):
        if time.perf_counter() >= deadline:
            return 0, None
        if site in selected:
            continue
        gain, loss = 0, removal_loss.copy()
        for point, value in covered:
            runner_up = second[point]
            if value <= runner_up:
                continue
            first, pos = near[point], owner[point]
            if value > first:
                gain += value - first
                loss[pos] -= first - runner_up
            else:
                loss[pos] -= value - runner_up
        minimum = min(loss)
        change = minimum - gain
        if change < best_delta:
            best_delta, best_swap = change, (loss.index(minimum), site)
    return best_delta, best_swap


class MySolver(Solver):
    def solve(self, instance, submit_candidate):
        k, m = instance.k, len(instance.sites)
        # Submit before doing expensive work: every k-subset of sites is valid.
        incumbent = list(range(k))
        receipt = submit_candidate({"sites": list(incumbent)})
        deadline = time.perf_counter() + max(0.0, receipt["remaining_s"]) - SAFETY_SECONDS
        if k == m or time.perf_counter() >= deadline:
            return {"sites": incumbent}

        table = dist_table(instance)
        weights = instance.weights
        rng = random.Random(12345)
        # An uncovered household pays the penalty regardless of this site.
        # Store only actual savings, so it costs no work inside each search pass.
        benefits = [[] for _ in range(m)]
        for point, (weight, row) in enumerate(zip(weights, table)):
            for site, distance in enumerate(row):
                value = weight * (instance.penalty - distance)
                if value > 0:
                    benefits[site].append((point, value))
        base_cost = instance.penalty * sum(weights)
        incumbent_cost = receipt["cost"]

        def keep(opened, cost):
            nonlocal incumbent, incumbent_cost
            if cost < incumbent_cost:
                incumbent, incumbent_cost = list(opened), cost
                submit_candidate({"sites": list(incumbent)})

        # Greedy: add the candidate with the largest reduction in total cost.
        opened = []
        near = [0] * instance.size
        selected = set()
        for _ in range(k):
            best_site, best_gain = None, -1
            for s, covered in enumerate(benefits):
                if time.perf_counter() >= deadline:
                    return {"sites": incumbent}
                if s in selected:
                    continue
                gain = sum(value - near[point] for point, value in covered
                           if value > near[point])
                if gain > best_gain:
                    best_gain, best_site = gain, s
            opened.append(best_site)
            selected.add(best_site)
            for point, value in benefits[best_site]:
                if value > near[point]:
                    near[point] = value
        keep(opened, base_cost - sum(near))

        local_minima = set()

        def descend(opened):
            while time.perf_counter() < deadline:
                state = frozenset(opened)
                # An already completed neighborhood has no improving exchange,
                # even if the same selected sites now have a different order.
                if state in local_minima:
                    return
                near = [0] * instance.size
                second = [0] * instance.size
                owner = [0] * instance.size
                for pos, s in enumerate(opened):
                    for point, value in benefits[s]:
                        if value > near[point]:
                            second[point] = near[point]
                            near[point] = value
                            owner[point] = pos
                        elif value > second[point]:
                            second[point] = value
                cost = base_cost - sum(near)
                keep(opened, cost)
                best_delta, best_swap = _best_swap(
                    benefits, opened, near, second, owner, deadline)
                if best_swap is None:
                    # A timed-out scan does not prove local optimality.
                    if time.perf_counter() < deadline:
                        local_minima.add(state)
                    return
                pos, s = best_swap
                opened[pos] = s
                # Preserve this improvement even if the next pass hits the limit.
                keep(opened, cost + best_delta)

        descend(opened)
        iteration = 0
        while time.perf_counter() < deadline:
            iteration += 1
            opened = list(incumbent)
            changes = 1 + iteration % min(k, 4)
            for pos in rng.sample(range(k), changes):
                closed = [s for s in range(m) if s not in opened]
                opened[pos] = rng.choice(closed)
            descend(opened)
        return {"sites": incumbent}
