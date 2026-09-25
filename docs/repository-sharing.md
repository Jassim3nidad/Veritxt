# Public repository sharing and co-developer setup

25 September candidate review: only two numeric aggregate CSVs were accepted from `smishguard_repo_update.zip`; [all 28 file decisions](../research/candidate_review/archive_review.json) and [review](../research/candidate_review/README.md) are recorded. Message-bearing fresh/parity files were excluded. Ignore/index protections now also cover arbitrary candidate export names, raw probes, data directories and common model binary formats. Ignore rules do not remove already tracked files; inspect the staged index and run the sharing checker before every commit. The two supplied aggregate CSVs preserve their original line endings through explicit attributes so their source hashes remain reproducible across checkouts.

The existing `Jassim3nidad/SMISHGUARD` repository is **public**. Share source, pinned dependencies, scripts, tests with synthetic fixtures, header-only templates, aggregate evidence and technical hashes. Do not commit raw/private messages, source downloads, reviewer assignments/answers, consent records, signed letters, credentials, local SDK/environment files, build outputs or caches.

The supplied model's redistribution provenance remains unresolved and its vocabulary contains two identifier-like numeric terms. Following the existing model/privacy review requirements, **its weights/vocabulary asset and model-bearing APK/source archives stay local**. Conversion code, model schema, safe parity probes and aggregate verification remain shareable. This restriction applies to public redistribution, not the authorized local offline development work. No weights are edited and no working local file is deleted.

`research/data/`, `research/runs/`, `deliverables/`, and main/development `assets/model.json` are ignored. Previously tracked generated deliverables are removed from the current Git tree without deleting local copies or rewriting history. Source packaging now excludes supplied production model assets. Do not attach the old model-bearing source archive to a public issue/release.

## After pulling

1. Use JDK 17 and the pinned Gradle wrapper; create local Android SDK configuration. `scripts/build.ps1` builds the default model-free debug app.
2. Create `research/.venv`, install `research/requirements.txt`, set `PYTHONPATH=research`, and run Python tests. These need no private dataset.
3. To reproduce local development-model parity, obtain the existing converted 0.2.0-dev asset through the team's authorized private channel and place it at `android/app/src/development/assets/model.json`. The asset remains ignored. Development builds now reject a missing or different asset; debug builds remain model-free. Use `scripts/build.ps1 -Variant development`. See [model installation investigation](model-install-investigation.md) for the required digest, regression check and verified private APK. Do not substitute the candidate under review.
4. Private review packets, raw datasets and consent records must use a controlled team handoff, never GitHub. Only the header templates and generator are included here.

Automatic warnings/reporting remain disabled. Physical-device testing remains pending. Pulling code or passing tests grants no dataset permission or research-performance status.

## Safe handoff sharing checks

The training demo ZIP, named dataset/model exports, SQLite databases/sidecars, joblib outputs and .env files are excluded from sharing. `python scripts/check_staged.py` reads only staged Git bytes and checks forbidden paths, credential patterns and mobile-number-like literals; it no longer opens local private datasets or models. This avoids accessing private source material merely to run a sharing check. It cannot recognize all arbitrary raw messages, so inspect every staged file and verify sanitized evidence with `python scripts/verify_safe_handoff.py` as well.

No source ZIP or APK release is part of this handoff. Archive checks inspect the two explicitly supplied safe ZIPs, local build membership and an in-memory archive of the reviewed Git index. Existing private deliverables are left untouched. Never attach a model-bearing APK to GitHub.
