# Monitor Placement: beginner guide and submission notes

The solution is already implemented in `adapters/mine.py`. It matched all six
published reference costs at every checkpoint and scored **100/100** on the included full
local public run. This is a measured public result, not a guarantee for the private
judge. Start by opening `demo.html`, then run the commands below.
Read `BENCHMARKS.md` for measured results and limitations.

## What the program solves

A city can afford only `k` air-quality monitors. The input gives household locations, the population at each location, and a separate list of allowed rooftops. The solver chooses exactly `k` rooftops so that as many people as possible have a nearby monitor, with particular importance given to places where more people live.

The returned answer is `{"sites": [candidate_id, ...]}`. Each ID must be a distinct integer from `0` to `len(instance.sites) - 1`. IDs refer to the allowed rooftop list, not to the household list. Returning a new coordinate or a household ID is not the required format. For example, if `k = 3`, a structurally valid answer could be `{"sites": [2, 7, 11]}` when those three candidate IDs exist.

For each household, the evaluator computes its distance to the nearest chosen monitor using `isqrt(dx*dx + dy*dy)`, which rounds the square-root distance down to an integer. If that integer distance is within the coverage radius `D`, it pays that distance. If it is greater than `D`, it pays the full penalty `P`. The total cost is the sum of `population × charged distance` over all households. **Lower cost is better.**

The cutoff matters: with `D = 100`, `P = 300`, and population `10`, integer distance `99` contributes `990`, while integer distance `101` contributes `3,000`. A point just beyond the radius is not charged its actual distance.

## How the solution works

The algorithm is a search heuristic for a facility-location problem. It does not need a trained AI model, internet access, an API key, or third-party Python packages.

1. Submit an immediately valid selection so that there is an answer before the first scoring checkpoint.
2. Precompute charged distances and store population-weighted savings only for
   households a candidate rooftop covers. Uncovered households have zero savings
   and do not need repeated evaluation during the search.
3. Build a stronger selection greedily: repeatedly add the rooftop that reduces the population-weighted cost most.
4. Improve it with swaps: replace one selected rooftop with one unselected rooftop whenever this reduces the cost. Repeat rather than stopping after the baseline's single swap.
5. Use small, general randomized changes to explore other selections, then repeat the swap search. Keep and submit the best answer found so far.
6. Stop before the deadline and return the best selection.

The efficient swap calculation stores each household's nearest and second-nearest selected rooftop. This avoids rebuilding the complete assignment separately for every possible removed rooftop. Randomness explores alternatives; the solver still evaluates every answer with the exact population-weighted objective. It does not look up answers by instance name or seed.

## What the benchmark checks

Each test allows a nominal **5-second solving budget**. Faster useful answers matter because the evaluator reads the best accepted answer at four checkpoints:

| Nominal checkpoint | Time | Weight in the instance score |
|---|---:|---:|
| 5% | 0.25 seconds | 10% |
| 20% | 1.00 second | 20% |
| 50% | 2.50 seconds | 30% |
| 100% | 5.00 seconds | 40% |

Implementation detail: the supplied `benchkit/budget.py` gives the final checkpoint a 5% grace window, so its actual final cutoff is **5.25 seconds**. The other three cutoffs remain as shown. Validation must finish before a cutoff for the candidate to count there; the solver should still finish within the nominal budget with a small safety margin.

At each checkpoint, the cost is compared with three published anchors: starter = `0.25`, baseline = `0.50`, and reference = `1.00`. Between anchors the score is interpolated linearly. A cost at or below the reference receives `1.00`; no accepted answer receives `0`. These numbers are quality scores, not classification accuracy.

The total is out of 100:

- **Quality, 70 points:** the mean weighted instance score across the test suite.
- **Robustness, 20 points:** the mean score across shifted, clustered cases. This component is halved if a family with at least two cases averages at least `0.75` while another such family averages below `0.50`.
- **Engineering, 10 points:** 5 points for valid results, 3 for runs without a crash or overrun, and 2 for accepted results by the first checkpoint. Each component is proportional to the fraction of cases meeting it.

Matching all final reference costs is strong evidence of solution quality, but it does not by itself imply 100/100. The earlier checkpoints also contribute to the score. The reference is an organizer benchmark; it is not stated to be a mathematical proof of the global optimum.

## Published public targets

The following values come from the repository's `public_reference.json`. They are **costs**, so smaller numbers are better. There is no separate universal pass mark stated in the problem README.

| Case | Family | Demand points | Candidate sites | Monitors `k` | Baseline cost | Reference cost to match or beat |
|---|---|---:|---:|---:|---:|---:|
| monitors-01 | uniform | 120 | 30 | 4 | 3,376,935 | 2,965,159 |
| monitors-02 | uniform | 200 | 50 | 6 | 4,392,304 | 4,230,218 |
| monitors-03 | uniform | 300 | 80 | 8 | 5,649,466 | 5,302,031 |
| monitors-04 | uniform | 400 | 110 | 10 | 6,941,054 | 6,442,771 |
| monitors-05 | clustered | 250 | 70 | 14 | 246,350 | 232,180 |
| monitors-06 | clustered | 400 | 100 | 20 | 320,676 | 309,586 |

There are six public cases: four uniform and two clustered. The README describes eight hidden cases: four uniform and four clustered, using unseen seeds. Clustered cases contain dense population clusters, unequal populations, and relatively few available rooftops inside those clusters. Passing the public cases cannot guarantee the hidden score. The final evaluation uses the organizers' isolated environment; local timings can vary.

## Files to keep together

`adapters/mine.py` is the solver submission. It works with the provided `adapter.py`, `data.py`, `validator.py`, `public_reference.json`, and `benchkit/` folder. The original starter, baseline, benchmark data, scoring rules, and anchors provide a reproducible comparison. `benchmarks/public_report.json` contains the full public report. `demo.py` provides a visual demonstration. `.vscode/` contains convenient VS Code tasks.

The submission entry point is `adapters.mine:MySolver`: the part before the colon is the module, and the part after it is the class defined in that module.

## Open and run in VS Code

1. Extract or open the complete submission folder in VS Code with **File → Open Folder**.
2. Open **Terminal → New Terminal**. Run commands from the `Monitor-Placement` folder containing `run.py`; do not run from its parent directory.
3. Check the interpreter with `python --version`. If that command is unavailable on Windows, try `py --version`. The project uses only Python's standard library.
4. Run the quick check, then the full public benchmark:

```text
python self_check.py --adapter adapters.mine:MySolver
python run.py --adapter adapters.mine:MySolver --suite public --out benchmarks/local_report.json
```

The self-check runs `monitors-01` and `monitors-05`. The full public run tests all six cases and writes a new local report, preserving the included measured report. Inspect accepted/rejected counts, crashes, overruns, checkpoint costs, and the score; a successful process exit alone does not mean every benchmark target was reached. You can also select **Terminal → Run Task** to use the included VS Code tasks.

To check the small correctness cases and recreate the visual demo:

```text
python -m unittest discover -s tests -v
python demo.py
```

Open `demo.html` in your browser. It compares baseline placement with the solver
on the first public case. Grey crosses are permitted sites, orange squares are
selected monitors, blue circles are covered demand, and red circles are missed
demand. The coordinates describe a synthetic grid, not a real geographic map.
Run scored benchmarks outside the debugger because debugging changes timing.

The upstream evaluator calls Unix process-management functions such as `os.setsid`, `os.getuid`, and `os.killpg` that are unavailable in native Windows Python. This package guards those three calls so the supplied runner can execute on Windows; the original runner is preserved in `upstream/runner_original.py`. The validator, instance generator, scoring formulas, anchors, and timing checkpoints are unchanged. Results from this package are local public benchmark results; the organizers determine the final score using their own environment. For the event submission, the required algorithm file is still `adapters/mine.py`, which works with the upstream Linux evaluator.

## Upload through GitHub or VS Code

For a submission into the original project, copy `adapters/mine.py` into the repository's existing `monitors/adapters/` folder. Include the solution explanation and any requested benchmark report. The original repository owner or event instructions determine the final destination and accepted upload format.

For your own GitHub repository using the website:

1. Sign in to GitHub and select **New repository**. Choose a name such as `Monitor-Placement-Solution` and create it.
2. Select **Add file → Upload files**. Upload the contents of the complete `Monitor-Placement` folder, retaining folders such as `adapters`, `benchkit`, and `benchmarks`. Do not upload only an empty folder or only a ZIP when reviewers need to inspect the code online.
3. Exclude `__pycache__` folders and `.pyc` files. Review the upload list, enter a commit message, and select **Commit changes**.
4. Verify that `adapters/mine.py`, the explanation, and the public benchmark report are visible in the repository. Share the repository URL when the organizers request it.

If Git is installed and you prefer VS Code:

1. Open the complete submission folder and select the **Source Control** icon.
2. If needed, select **Initialize Repository**.
3. Review the files and stage the intended submission, explanation, and reports. A `.gitignore` should exclude `__pycache__/` and `*.pyc`.
4. Enter a commit message such as `Add Monitor Placement solver and public benchmark results`, then select **Commit**.
5. Select **Publish Branch** or **Publish to GitHub**, sign in if requested, and choose the destination repository.
6. Open the uploaded repository and verify that `adapters/mine.py` and the explanation are present. Share that repository URL when requested by the organizers.

If the organizers request only an adapter file, submit the solver file rather than assuming that uploading a new repository completes registration. If they request a fork or pull request, follow that workflow. The problem statement does not specify an event-specific registration form or upload destination.

The local folder uses branch `main` and is connected to
[your Monitor-Placement repository](https://github.com/Vaishnavi-Naga-Sai-Ravula/Monitor-Placement).
For later changes, review `git status`, stage the intended files, commit them,
then run `git push`. Local benchmark reruns named `benchmarks/local_*.json` are
ignored; the included reproducible report is `benchmarks/public_report.json`.

For a separate empty GitHub repository, use these commands after committing the
project, replacing the sample remote URL with that repository's URL:

```text
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Create the remote repository without an initial README, license, or `.gitignore`
when using that push workflow. If you want to publish as `main`, you can choose
that branch name before pushing. See [GitHub's import guide](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).

## Source of the rules

- [Original Monitor Placement README](https://github.com/Vaishnavi-Naga-Sai-Ravula/Algo-Ranabhoomi-Phase_1/blob/main/monitors/README.md)
- [Published public anchors](https://github.com/Vaishnavi-Naga-Sai-Ravula/Algo-Ranabhoomi-Phase_1/blob/main/monitors/public_reference.json)
- [Input generator and suite](https://github.com/Vaishnavi-Naga-Sai-Ravula/Algo-Ranabhoomi-Phase_1/blob/main/monitors/data.py)
- [Plan validator](https://github.com/Vaishnavi-Naga-Sai-Ravula/Algo-Ranabhoomi-Phase_1/blob/main/monitors/validator.py)
- [Checkpoint timing](https://github.com/Vaishnavi-Naga-Sai-Ravula/Algo-Ranabhoomi-Phase_1/blob/main/monitors/benchkit/budget.py)
- [Scoring curve](https://github.com/Vaishnavi-Naga-Sai-Ravula/Algo-Ranabhoomi-Phase_1/blob/main/monitors/benchkit/scoring.py)
- [Score aggregation](https://github.com/Vaishnavi-Naga-Sai-Ravula/Algo-Ranabhoomi-Phase_1/blob/main/monitors/benchkit/aggregate.py)
- [Evaluation boundary and hidden judging](https://github.com/Vaishnavi-Naga-Sai-Ravula/Algo-Ranabhoomi-Phase_1/blob/main/monitors/SECURITY.md)
