"""Create an offline visual demo from one synthetic public instance."""
import html
import json
import math
import time
from pathlib import Path

import data
from adapters.baseline import BaselineSolver
from adapters.mine import MySolver
from adapter import dist_table
from validator import validate


def solve_for_demo(instance, solver):
    started, best_cost, best_plan = time.perf_counter(), None, None
    history = []

    def submit(plan):
        nonlocal best_cost, best_plan
        cost, reason = validate(instance, plan)
        elapsed = time.perf_counter() - started
        if cost is not None and elapsed <= 5.25 and (best_cost is None or cost < best_cost):
            best_cost = cost
            best_plan = {"sites": list(plan["sites"])}
            history.append([round(elapsed, 6), cost])
        return {"accepted": cost is not None and elapsed <= 5.25, "reason": reason,
                "cost": cost, "best": best_cost, "elapsed_s": elapsed,
                "remaining_s": 5.0 - elapsed}

    submit(solver.solve(instance, submit))
    return best_plan, best_cost, history


def map_svg(instance, plan, title):
    chosen = plan["sites"]
    table = dist_table(instance)
    parts = ['<svg viewBox="0 0 540 555" role="img" aria-label="' + html.escape(title) + '">',
             '<rect width="540" height="555" fill="#f8fafc" rx="12"/>']
    scale = .46

    def pos(xy):
        return 40 + xy[0] * scale, 500 - xy[1] * scale

    for tick in range(0, 1001, 200):
        x, y = pos((tick, tick))
        parts.append(f'<path d="M{x} 40 V500 M40 {y} H500" stroke="#e2e8f0"/>')
    for site in chosen:
        x, y = pos(instance.sites[site])
        parts.append(f'<circle cx="{x}" cy="{y}" r="{instance.radius * scale}" fill="#dbeafe" fill-opacity=".16" stroke="#93c5fd" stroke-dasharray="4 4"/>')
    for site, xy in enumerate(instance.sites):
        x, y = pos(xy)
        parts.append(f'<path d="M{x-3} {y} H{x+3} M{x} {y-3} V{y+3}" stroke="#94a3b8"/>')
    for point, (xy, weight, row) in enumerate(zip(instance.points, instance.weights, table)):
        nearest = min(chosen, key=row.__getitem__)
        missed = row[nearest] == instance.penalty
        x, y = pos(xy)
        sx, sy = pos(instance.sites[nearest])
        if not missed:
            parts.append(f'<path d="M{x} {y} L{sx} {sy}" stroke="#cbd5e1" stroke-width=".5"/>')
        fill = '#e11d48' if missed else '#2563eb'
        radius = min(8, 1.5 + math.sqrt(weight) * .6)
        parts.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" fill-opacity=".75"><title>Demand point {point}; population {weight}; charged distance {row[nearest]}</title></circle>')
    for site in chosen:
        x, y = pos(instance.sites[site])
        parts.append(f'<rect x="{x-5}" y="{y-5}" width="10" height="10" fill="#f59e0b" stroke="#92400e"><title>Selected candidate {site}</title></rect>')
    parts.append(f'<text x="40" y="535" fill="#475569" font-size="13">{html.escape(title)}</text></svg>')
    return ''.join(parts)


def main():
    entry = data.PUBLIC_SUITE[0]
    instance = data.make_instance(entry.seed, entry.profile, entry.name)
    baseline_plan, baseline_cost, _ = solve_for_demo(instance, BaselineSolver())
    best_plan, best_cost, history = solve_for_demo(instance, MySolver())
    saving = 100 * (baseline_cost - best_cost) / baseline_cost
    content = f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monitor Placement — Solver Demo</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1160px;margin:32px auto;padding:0 20px;color:#0f172a;background:#fff}}h1{{font-size:32px;margin-bottom:8px}}p{{line-height:1.6}}.maps{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}svg{{width:100%;height:auto}}.card{{padding:16px;background:#f1f5f9;border-radius:12px}}code{{background:#e2e8f0;padding:3px 6px;border-radius:4px}}@media(max-width:700px){{.maps{{grid-template-columns:1fr}}}}</style>
<h1>Better air-quality monitor placement</h1>
<p>Choose {instance.k} of {len(instance.sites)} permitted sites for {instance.size} population-weighted demand points. This is the synthetic public case <code>{entry.name}</code>.</p>
<div class="card"><strong>{saving:.2f}% lower cost</strong> than the published baseline: {baseline_cost:,} → {best_cost:,}. Lower is better.</div>
<div class="maps"><div><h2>Published baseline</h2>{map_svg(instance, baseline_plan, 'Greedy + one best swap')}</div><div><h2>Our solver</h2>{map_svg(instance, best_plan, 'Repeated swaps + perturbed restarts')}</div></div>
<p><span style="color:#2563eb">●</span> covered demand; <span style="color:#e11d48">●</span> missed demand; larger circles indicate larger population. Orange squares are selected monitors; grey crosses are permitted sites. Hover over markers for values.</p>
<p>The scored distance is the integer square root of squared distance. Distances above radius {instance.radius} receive penalty {instance.penalty}; the drawn coverage circles are approximate. The full public benchmark report is in <code>benchmarks/public_report.json</code>. This visual demo is not a private judging result.</p>
<p>Selected candidate IDs: <code>{', '.join(map(str, best_plan['sites']))}</code></p>
</html>'''
    root = Path(__file__).resolve().parent
    (root / 'demo.html').write_text(content, encoding='utf-8')
    (root / 'benchmarks' / 'demo_plan.json').write_text(json.dumps({
        'instance': instance.name, 'baseline_plan': baseline_plan, 'baseline_cost': baseline_cost,
        'solver_plan': best_plan, 'solver_cost': best_cost, 'history': history,
        'note': 'Direct visual-demo run; use run.py for benchmark scoring.'}, indent=2), encoding='utf-8')
    print(f'Demo saved: {root / "demo.html"}')
    print(f'Baseline: {baseline_cost:,}; solver: {best_cost:,}; improvement: {saving:.2f}%')


if __name__ == '__main__':
    main()
