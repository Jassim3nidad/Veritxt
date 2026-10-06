# SmishGuard presentation comparison — 5 October 2026

Preliminary retrospective evaluation: 3,340 source-supported records; identical 448-record test; source/rule labels awaiting independent confirmation.

| Algorithm | Phishing precision | Recall | F1 | Accuracy | Warm median (emulator) | APK size | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Logistic Regression | 96.88% | 55.36% | 70.45% | 94.20% | 0.302 ms | 12.94 MB | trained, evaluated, APK verified |
| Multinomial NB | 83.33% | 35.71% | 50.00% | 91.07% | 0.286 ms | 12.94 MB | trained, evaluated, APK verified |
| Linear SVM | 98.00% | 87.50% | 92.45% | 98.21% | 0.314 ms | 12.93 MB | trained, evaluated, APK verified |
| mBERT | 100.00% | 41.07% | 58.23% | 92.63% | 154.173 ms | 1511.96 MB | trained, evaluated, APK verified |

Use “Model score,” not a validated probability. Report abstention separately. Most records have historical exposure; old/new scores cannot alone show improvement. Emulator timing is not physical-phone timing. mBERT is full float32 multilingual BERT.

[Full results, limitations and APK hashes](four-model-comparison-20261005.md) · [Machine-readable metrics](expanded-four-model-results-20261005.json) · [Verification](expanded-four-model-verification-20261005.json) · [Benchmark conditions](expanded-four-model-benchmark-20261005.json).

Actual fictional-message screenshots: local `deliverables/expanded-20261005/screenshots/`. Show the same English phishing example and benign Taglish example in all four apps; retain any false positives or negatives.
