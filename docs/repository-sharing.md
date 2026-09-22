# Public repository sharing and co-developer setup

The existing `Jassim3nidad/SMISHGUARD` repository is **public**. Share source, pinned dependencies, scripts, tests with synthetic fixtures, header-only templates, aggregate evidence and technical hashes. Do not commit raw/private messages, source downloads, reviewer assignments/answers, consent records, signed letters, credentials, local SDK/environment files, build outputs or caches.

The supplied model's redistribution provenance remains unresolved and its vocabulary contains two identifier-like numeric terms. Following the existing model/privacy review requirements, **its weights/vocabulary asset and model-bearing APK/source archives stay local**. Conversion code, model schema, safe parity probes and aggregate verification remain shareable. This restriction applies to public redistribution, not the authorized local offline development work. No weights are edited and no working local file is deleted.

`research/data/`, `research/runs/`, `deliverables/`, and main/development `assets/model.json` are ignored. Previously tracked generated deliverables are removed from the current Git tree without deleting local copies or rewriting history. Source packaging now excludes supplied production model assets. Do not attach the old model-bearing source archive to a public issue/release.

## After pulling

1. Use JDK 17 and the pinned Gradle wrapper; create local Android SDK configuration. `scripts/build.ps1` builds the default model-free debug app.
2. Create `research/.venv`, install `research/requirements.txt`, set `PYTHONPATH=research`, and run Python tests. These need no private dataset.
3. To reproduce local development-model parity, obtain the original package through the team's authorized private channel. Follow the audit/conversion commands in research/README.md. The generated development asset remains ignored. Without it, the app correctly remains in its missing-model state; model-specific instrumentation needs the asset.
4. Private review packets, raw datasets and consent records must use a controlled team handoff, never GitHub. Only the header templates and generator are included here.

Automatic warnings/reporting remain disabled. Physical-device testing remains pending. Pulling code or passing tests grants no dataset permission or research-performance status.
