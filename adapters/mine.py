"""Greedy construction, repeated fast swaps, and perturbed restarts.

Only valid site selections are submitted. There are no third-party dependencies,
instance-name checks, reference-cost lookups, or changes to the evaluator.
"""
import random
import time

from adapter import Solver, dist_table

SAFETY_SECONDS = 0.20


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

        def cost_of(opened):
            return sum(w * min(row[s] for s in opened)
                       for w, row in zip(weights, table))

        incumbent_cost = cost_of(incumbent)

        def keep(opened, cost):
            nonlocal incumbent, incumbent_cost
            if cost < incumbent_cost:
                incumbent, incumbent_cost = list(opened), cost
                submit_candidate({"sites": list(incumbent)})

        # Greedy: add the candidate with the largest reduction in total cost.
        opened = []
        near = [instance.penalty] * instance.size
        for _ in range(k):
            best_site, best_cost = None, float("inf")
            for s in range(m):
                if time.perf_counter() >= deadline:
                    return {"sites": incumbent}
                if s in opened:
                    continue
                cost = sum(w * (row[s] if row[s] < d else d)
                           for w, row, d in zip(weights, table, near))
                if cost < best_cost:
                    best_cost, best_site = cost, s
            opened.append(best_site)
            near = [min(d, row[best_site]) for d, row in zip(near, table)]
        keep(opened, sum(w * d for w, d in zip(weights, near)))

        def descend(opened):
            while time.perf_counter() < deadline:
                selected = set(opened)
                near, second, owner = [], [], []
                for row in table:
                    best, nxt, own = instance.penalty, instance.penalty, 0
                    for pos, s in enumerate(opened):
                        d = row[s]
                        if d < best:
                            best, nxt, own = d, best, pos
                        elif d < nxt:
                            nxt = d
                    near.append(best)
                    second.append(nxt)
                    owner.append(own)
                cost = sum(w * d for w, d in zip(weights, near))
                keep(opened, cost)
                best_delta, best_swap = 0, None
                for s in range(m):
                    if time.perf_counter() >= deadline:
                        return
                    if s in selected:
                        continue
                    # Common gain from opening s, plus each owner's removal loss.
                    delta, loss = 0, [0] * k
                    for row, w, a, b, own in zip(table, weights, near, second, owner):
                        d = row[s]
                        if d < a:
                            delta += w * (d - a)
                        else:
                            loss[own] += w * ((d if d < b else b) - a)
                    pos = min(range(k), key=loss.__getitem__)
                    change = delta + loss[pos]
                    if change < best_delta:
                        best_delta, best_swap = change, (pos, s)
                if best_swap is None:
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
