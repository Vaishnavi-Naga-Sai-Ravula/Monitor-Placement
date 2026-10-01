# Original source and compatibility

Source: [public Monitor Placement bundle](https://github.com/Vaishnavi-Naga-Sai-Ravula/Algo-Ranabhoomi-Phase_1/tree/main/monitors), retrieved on 1 October 2026. All 23 original source files are included. `upstream/source_manifest.json` records their original SHA-256 hashes.

The supplied files `data.py`, `validator.py`, `public_reference.json`, the
starter/baseline, and all scoring/anchor/timing code are unchanged. The added
algorithm lives only in `adapters/mine.py` and never imports the reference JSON.

Two original files have documented local changes:

1. `README.md` has a solution introduction. Its complete original content is
   preserved in `upstream/README_original.md` and below the new introduction.
2. `benchkit/runner.py` adds `os.name == "posix"` guards around `os.setsid()`,
   `os.getuid()`, and `os.killpg()`. This allows native Windows execution while
   preserving the original Linux behavior. The exact upstream version is
   `upstream/runner_original.py`.

The parent still validates candidates, measures time after validation,
enforces deadlines and submission limits, verifies instance digests, and
computes the score. No benchmark targets or scoring formulas were changed.

On Windows, process termination covers the direct solver process. The official
Linux evaluator additionally supports process-group termination and supported
memory/privilege restrictions. This solver does not start subprocesses. The
organizers' environment and private suite determine the final event result.

If an organizer supplies the harness, submit `adapters/mine.py` against that
harness. Do not replace their benchmark files or regenerate their reference
anchors. Their stated upload workflow takes precedence over this guide.
