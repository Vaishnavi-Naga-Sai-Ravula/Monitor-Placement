# Benchmark targets and measured results

On 1 October 2026, the included `adapters.mine:MySolver` was run on all six
public cases with the supplied process-isolated evaluator, using only the
three documented Windows compatibility guards. Python 3.13, native Windows,
`budget_scale = 1.0`, nominal 5 seconds per case. Three consecutive full local
public runs scored 100/100; these are not official private judging results.

**All six reference costs were matched at every checkpoint. Total: 100/100.**

| Public case | Baseline cost | Published reference | Our final cost | Target | Weighted instance score |
|---|---:|---:|---:|---|---:|
| monitors-01 | 3,376,935 | 2,965,159 | 2,965,159 | Matched | 1.0000 |
| monitors-02 | 4,392,304 | 4,230,218 | 4,230,218 | Matched | 1.0000 |
| monitors-03 | 5,649,466 | 5,302,031 | 5,302,031 | Matched | 1.0000 |
| monitors-04 | 6,941,054 | 6,442,771 | 6,442,771 | Matched | 1.0000 |
| monitors-05 | 246,350 | 232,180 | 232,180 | Matched | 1.0000 |
| monitors-06 | 320,676 | 309,586 | 309,586 | Matched | 1.0000 |

Lower cost is better. The exact public targets are in `public_reference.json`.
The full measured history and checkpoint costs are in
`benchmarks/public_report.json`; the repeat is preserved separately in
`benchmarks/public_repeat_report.json`; a third run is in
`benchmarks/public_consistency_report.json`.

| Score component | Measured | Maximum |
|---|---:|---:|
| Quality | 70.0000 | 70 |
| Robustness | 20.0000 | 20 |
| Engineering | 10.0000 | 10 |
| Total | 100.0000 | 100 |

There were **zero rejected candidates, zero crashes, zero overruns**, and a
valid candidate before the first checkpoint in every case. The two-case
self-check also completed successfully (100/100 on that subset). Six
correctness tests passed, including exact comparison on a small case,
population weighting, the integer-distance cutoff, uncovered points,
selection of all candidates, and the exhausted-budget fallback. The exchange
calculation was also compared with every brute-force neighbor on 40 randomized
small cases, covering tied distances and zero weights.

## How the public score reached 100

The earlier solver reached every final target but lost points at early
checkpoints, producing scores around 99.6-99.7 on some local runs. The updated
solver represents each candidate by population-weighted savings for covered
households only. Greedy selection and exchanges skip all zero-savings pairs,
while preserving the exact objective and search decisions. Completed local
optima are cached so repeated selections do not rescan the same neighborhood.
The swap loop also skips savings that cannot affect its result. No public answers,
case names or reference costs are used to choose plans. The evaluator and its
budgets are unchanged.

On the included run, `monitors-04` reached its reference at about 0.12 seconds,
before the first 0.25-second checkpoint. Every case matched its target by that
first checkpoint. All later checkpoint costs matched as well. Across the
three consistency runs, this case reached its target in 0.069-0.120 seconds.

The scoring checkpoints are at 0.25, 1.0, 2.5, and nominally 5.0 seconds.
The actual final cutoff includes a 5% grace window and is 5.25 seconds.
They have weights 0.10, 0.20, 0.30, 0.40. Matching every **final** reference cost
does not imply matching every checkpoint; a 100-point public result requires
full quality at all checkpoints, plus robustness and engineering points.

At each checkpoint, starter cost corresponds to 0.25, baseline to 0.50,
and reference to 1.00, with linear interpolation between those anchors.
The mean instance score gives 70 quality points. Shifted clustered cases
give 20 robustness points, subject to the documented specialization penalty.
Validity, clean completion, and an early candidate give 10 engineering points.
The source states no universal pass threshold.

## Public targets versus hidden benchmarks

The public bundle contains six generated cases. The README describes eight
private cases with unseen seeds, but their actual instances, anchors, and
the reference solver are absent. No one can honestly certify those unseen
benchmarks from this public bundle. The supplied solver uses input
coordinates/populations and general search; it never loads public anchor
answers or checks instance names.

Reference anchors were generated with an unpublished solver at 10 times
the contestant budget (`reference_scale = 10`). A reference cost is a
comparison target, not a proof of the mathematical optimum. Timing and
early-checkpoint results may differ on the organizers' machine or when
background tasks compete for CPU time. Run one benchmark at a time, outside
the debugger; the reports record measured scores rather than fixed guarantees.

## Reproduce the measurements

From the folder containing `run.py`:

```text
python self_check.py --adapter adapters.mine:MySolver
python run.py --adapter adapters.mine:MySolver --out benchmarks/local_report.json
python -m unittest discover -s tests -v
```

Keep the included measured report as evidence; the command above writes
your new result separately. Use the normal budget for any score claims.
The full benchmark takes roughly half a minute plus process-startup time.
The `wall_s` report field includes startup; the solving budget begins only
after the solver child reports that it is ready.

Do not regenerate reference anchors or edit the costs, validator, score,
generator, or budget to improve a submission. For the official judge,
provide `adapters/mine.py` with its class name `MySolver` and use their harness.

Sources: [published anchors](https://github.com/Vaishnavi-Naga-Sai-Ravula/Algo-Ranabhoomi-Phase_1/blob/main/monitors/public_reference.json),
[scoring](https://github.com/Vaishnavi-Naga-Sai-Ravula/Algo-Ranabhoomi-Phase_1/blob/main/monitors/benchkit/scoring.py),
[aggregation](https://github.com/Vaishnavi-Naga-Sai-Ravula/Algo-Ranabhoomi-Phase_1/blob/main/monitors/benchkit/aggregate.py),
[anchor generation](https://github.com/Vaishnavi-Naga-Sai-Ravula/Algo-Ranabhoomi-Phase_1/blob/main/monitors/benchkit/anchors.py).
