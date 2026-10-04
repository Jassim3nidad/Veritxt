"""Publish only aggregate experiment and APK verification evidence."""
import json
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/'research/data/expanded-20261005'
RUN=PRIVATE/'experiment-v1'
DOCS=ROOT/'docs'
NAMES=('lr','nb','svm','mbert')
TITLES={'lr':'Logistic Regression','nb':'Multinomial NB','svm':'Linear SVM','mbert':'mBERT'}

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def write(path,value):path.write_text(json.dumps(value,indent=2),encoding='utf-8')
def pct(value):return f'{100*value:.2f}'

def main():
    aggregate=read(RUN/'four-model-aggregate.json');prep=aggregate['preparation'];results=aggregate['results']
    baseline=read(RUN/'baseline-freeze.json');bert=read(RUN/'mbert/training-summary.json');lengths=read(RUN/'mbert/length-audit.json')
    extra=read(RUN/'extra-audit.json');workbook=read(PRIVATE/'workbook-audit.json');hardware=read(PRIVATE/'hardware.json')
    benchmark=read(PRIVATE/'common-device-benchmark.json')
    verification={};artifacts={};training={}
    for name in NAMES:
        v=read(PRIVATE/f'verification-{name}.json');e=read(PRIVATE/f'emulator-{name}.json')
        if v['build']['exit_code'] or v['emulator']['exit_code'] or v['package']['exit_code']:raise ValueError('Unverified APK')
        v['emulator_tests']={k:int(re.search(r'OK \((\d+) tests?\)',text).group(1)) for k,text in e.items() if isinstance(text,str) and re.search(r'OK \((\d+) tests?\)',text)}
        v['emulator_test_total']=sum(v['emulator_tests'].values());v['emulator_status']=e.get('status')
        v['parity']=read(RUN/'mbert/export-aggregate.json') if name=='mbert' else read(RUN/name/'parity-summary.json')
        verification[name]=v
        artifacts[name]=read(ROOT/f'deliverables/expanded-20261005/{name}-apk-manifest.json')
        assets=ROOT/f'android/app/src/{name}/assets';artifacts[name]['asset_bundle_bytes']=sum(p.stat().st_size for p in assets.iterdir() if p.is_file())
        training[name]=bert if name=='mbert' else baseline['validation'][name]
        # A failed Windows API call returned zero; zero is not a memory measurement.
        if not training[name].get('process_peak_working_set_bytes'):
            training[name]['process_peak_working_set_bytes']=None
            training[name]['process_memory_note']='Unavailable: initial Windows process-memory probe returned zero; CPU duration / CUDA peaks are reported separately.'
    aggregate.update(training=training,extra_audit=extra,review_workbook=workbook,hardware=hardware,mbert_length_audit=lengths,artifacts=artifacts)
    write(DOCS/'expanded-four-model-results-20261005.json',aggregate)
    write(DOCS/'expanded-four-model-verification-20261005.json',verification)
    write(DOCS/'expanded-four-model-benchmark-20261005.json',benchmark)
    lines=['# SmishGuard expanded four-model comparison — 5 October 2026','',
        'All four models were trained, evaluated, exported and verified in separate offline Android APKs. This remains preliminary development evidence using source/rule labels and substantially exposed messages. No final algorithm winner, independent prospective validation or physical-phone performance is claimed.','',
        '## Dataset, scope and review','',
        'The supplied package reports adviser-directed expansion to all SMS phishing; that statement is recorded without independently verifying adviser approval. Positives describe deceptive phishing attempts; negatives are purported genuine messages. Advertising and job/loan fraud remain excluded. Eighteen excluded job/loan records have possible phishing signals and require scope adjudication; none was silently relabeled or included as ham.','',
        'The CSV matches all reported counts: **3,552 included, 468 smishing, 3,084 ham, 2,594 supplied template groups, 71 flags, and 2,272 excluded** (1,950 advertising / 322 fraud). There are no duplicate IDs, cleaned exact duplicates, conflicting redacted labels, mixed-label supplied groups or template-key mismatches. Missing sender/date values are 261/60; all prediction-text, label and grouping fields are populated. Included and excluded files have zero cleaned-exact overlap. Raw sources are absent from the ZIP, so this validates the CSV and matching source snapshots, not a reproduced original build. The unchanged original package and builder remain private.','',
        '**Used: 3,340 records (393 smishing, 2,947 ham). Held: 212** — 60 GitHub records with unresolved permission evidence, 13 team/social records with unresolved origin/consent/use evidence, and 139 automated privacy holds. No new permission or independent human annotation is inferred. All 71 flagged and 300 validation-review entries have blank labeler/final-label fields; 59 supplied flags survive in the eligible subset. Every eligible record still awaits independent label/privacy review.','',
        '| Pinned source | Used ham | Used smishing | Local research basis |','|---|---:|---:|---|']
    licenses={'tagalog':'ZERO v1, CC0 1.0','marketing':'Scott Lee Chua v15, CC BY 4.0','bwandowando':'BwandoWando v49, CC BY-NC-SA 4.0; noncommercial local use'}
    for s,values in extra['eligible_source_counts'].items():lines.append(f'| {s} | {values.get("ham",0)} | {values.get("smishing",0)} | {licenses[s]} |')
    lines+=['','[Existing attribution/source evidence](source-evidence.md) is retained. The new view uses direct cleaned matches to pinned source copies, automated URL/email/digit minimization and conservative privacy holds. Human redaction review and original acquisition/consent are not established. No raw text, source/sender/ID/date/review metadata is supplied as a prediction feature; only redacted text is used. Package IDs are version-specific and mapped to private content fingerprints.','',
        '## Frozen partitions and exposure','',
        '| Partition | Records | Ham | Smishing | Groups | Positive groups |','|---|---:|---:|---:|---:|---:|']
    for part,s in prep['partition_support'].items():lines.append(f'| {part} | {s["records"]} | {s["ham"]} | {s["smishing"]} | {s["groups"]} | {s["positive_groups"]} |')
    lines+=['',f'The label-blind audit merged {prep["merged_supplied_groups"]} supplied groups, producing {prep["retained"]["groups"]} components. All six partition-pair group-overlap counts are zero. Deterministic SequenceMatcher >=0.85 and supplied-template unions reduce near-copy leakage, but cannot establish perfect semantic independence. Calibration and each evaluation partition meet the predeclared >=20 positives / >=10 positive-group floor; grouped CV fallback was unnecessary.','',
        'Exactly 1,032 eligible messages match the cleaned original-source text of the previous experiment (555 training, 159 validation, 165 calibration, 153 test); eight corresponding labels changed. The broader normalized exact/near-copy audit finds **3,269/3,340** exposed to earlier supplied training corpora or previous partitions. The 71 unmatched messages are not certified unseen. Historical full-data training membership is incomplete.','',
        f'The new test has {aggregate["test_exposure"]["known_overlap"]}/{aggregate["test_exposure"]["records"]} records with detected historical overlap. New package IDs and this new split do not reset exposure. GitHub-source evaluation is held because its permitted use is unresolved.','',
        f'Dataset SHA-256: `{prep["dataset_sha256"]}`. Split SHA-256: `{prep["split_sha256"]}`. Cased-view SHA-256: `{prep["case_view_sha256"]}`. Public fingerprints identify whole manifests; row-level membership and fingerprints remain private.','',
        '## Training and final evaluation','',
        'LR/NB/SVM reuse sg-ascii-v1 and raw-count unigram TF-IDF with smooth IDF and L2 normalization. Five grouped training folds select parameters with TF-IDF fitted afresh inside every fold. Only training records fit the final pipeline. Sigmoid calibration is fitted once on calibration records; thresholds maximize validation F1 with the predeclared tie rule. All four pipelines were frozen before opening final test predictions.','',
        f'mBERT fine-tuned `google-bert/bert-base-multilingual-cased`, revision `3f076fdb1ab68d5b2880cb87a0886f315b8146f8`, matching tokenizer, new binary head, all {bert["trainable_parameters"]:,} parameters trainable. Two epochs, seed 20261005, Adafactor 2e-5, batch 1 / accumulation 8, gradient checkpointing and float16 CUDA autocast; selected epoch {bert["selected_epoch"]} by validation AP. Checkpoints include optimizer/scaler/RNG for resumption. The training-only p95 of {lengths["p95"]:.2f} tokens selected **{lengths["selected_length"]} tokens**: {lengths["truncated_at_selected"]}/{lengths["records"]} truncated versus {lengths["truncated_at_128"]} at 128. Training used {bert["seconds"]:.2f} seconds of a 2,700-second budget, with {bert["peak_cuda_bytes"]:,} peak allocated CUDA bytes on the RTX 3050 Laptop 4 GiB. This is a bounded configuration, not an exhaustive BERT search.','',
        'All rows below use the identical 448 test records (392 ham, 56 smishing), 251 groups and 25 positive-bearing groups. Percentages are shown; confusion entries are counts.','',
        '| Model | Precision | Recall | Phishing F1 | Macro-F1 | Accuracy | FPR | TN / FP / FN / TP |','|---|---:|---:|---:|---:|---:|---:|---|']
    for n in NAMES:
        r=results[n];conf=' / '.join(str(r['confusion'][k]) for k in ('tn','fp','fn','tp'))
        lines.append('| '+TITLES[n]+' | '+' | '.join(pct(r[k]) for k in ('precision','recall','f1','macro_f1','accuracy','false_positive_rate'))+' | '+conf+' |')
    best=max(NAMES,key=lambda n:results[n]['f1'])
    lines+=['',f'{TITLES[best]} has the highest observed phishing F1 in this run. This does not establish a final winner. The older experiment has different membership, labels and scope; score differences alone cannot establish improvement. Unfavorable predictions are retained and no test-based retuning followed.','',
        '| Model | Threshold | F1 95% group interval | Brier | Log loss | Training seconds | Model bundle bytes | APK bytes |','|---|---:|---|---:|---:|---:|---:|---:|']
    for n in NAMES:
        r=results[n];ci=r['confidence_intervals']['intervals']['f1']
        lines.append(f'| {TITLES[n]} | {r["threshold"]:.2f} | {ci["low"]:.4f}–{ci["high"]:.4f} | {r["brier"]:.5f} | {r["log_loss"]:.5f} | {training[n]["seconds"]:.3f} | {artifacts[n]["asset_bundle_bytes"]:,} | {artifacts[n]["apk_bytes"]:,} |')
    lines+=['','Intervals use 2,000 group resamples, conditional on fixed fitted models. They omit fitting/selection uncertainty and multiple-comparison correction. Imperfect groups, source sampling and unconfirmed labels further limit inference. A zero-FPR sample or degenerate interval does not prove zero population false positives. Validation is reused for selection and threshold choice. Brier/log loss and [reliability plots](expanded-reliability-20261005.png) measure agreement with inherited labels, not validated real-world probabilities. Baseline CPU durations are measured; their failed process-memory probes are marked unavailable, not zero usage.','',
        '| Paired F1 difference | 95% group interval |','|---|---|']
    for pair,ci in aggregate['paired_f1']['intervals'].items():lines.append(f'| {pair} | {ci["low"]:.4f} to {ci["high"]:.4f} |')
    lines+=['','Full class/group support, all metric intervals, reliability-bin counts and language/category/source breakdowns are in the [aggregate results](expanded-four-model-results-20261005.json). Subgroup metrics require >=20 records and >=5 per class, otherwise only support is reported. Languages are supplied rough guesses. Categories partly derive from label rules and are descriptive, not independent annotation.','',
        '## Offline app verification and presentation','',
        'The minimalist UI, Model score wording, privacy controls and abstention behavior are preserved. Reporting and automatic warnings remain disabled. All APKs have no INTERNET permission, verified signatures, correct distinct package IDs and matching bundled model hashes. Old model assets, app/test APKs and rollback deliverables remain local and unchanged. The mBERT export is faithful float32 ONNX with the original multilingual architecture; there is no quantization or replacement.','',
        '| Model | Build / lint | JVM tests (skipped) | Emulator tests | Python/export parity cases | Test app coverage |','|---|---|---:|---:|---:|---|']
    for n in NAMES:
        v=verification[n];dep=results[n]['deployment']
        lines.append(f'| {TITLES[n]} | passed / {v["lint"].get("Error",0)} errors | {v["jvm"]["tests"]} ({v["jvm"]["skipped"]}) | {v["emulator_test_total"]} | {v["parity"]["cases"]} | {dep["scored"]}/{dep["records"]} |')
    lines+=['','Seventy-five research tests, 20 existing model guards and six expanded-protocol guards passed. Emulator checks cover offline paste/share, actual model loading, missing/invalid models, long/empty/random inputs, English/Taglish, repeated scans, permissions and lifecycle/privacy. JVM/Android parity verifies actual fitted exports, class decisions and exactly-once calibration; mBERT additionally checks token IDs, masks, token types and full logits within predeclared tolerances. [Detailed verification](expanded-four-model-verification-20261005.json).','',
        'Classifier metrics above score every test record. App-policy coverage is separate and never credits an abstention as a correct negative. The four identical fictional benchmark probes deliberately include short text; their coverage is reported separately from research-test coverage. Actual screenshots are in local `deliverables/expanded-20261005/screenshots/<algorithm>/`, with the same fictional messages for all models.','',
        '| Model | Cold detector load ms | Warm median ms | Warm p95 ms | Scored / 200 scans |','|---|---:|---:|---:|---:|']
    for n in NAMES:
        b=benchmark['results'][n];cold=b.get('cold_detector_ms',b.get('model_load_ms'))
        lines.append(f'| {TITLES[n]} | {cold:.3f} | {b["p50_ms"]:.3f} | {b["p95_ms"]:.3f} | {b["scored"]} |')
    lines+=['','All four were benchmarked in one session of `SmishGuard_Comparison_API36` (API 36 x86_64, four virtual CPUs, 4096 MiB configured RAM). Host: Intel i5-11400H, approximately 24 GiB RAM, Windows 11. Airplane mode on, Wi-Fi off, one app process active, four fixed probes, 20 warmups, 200 scans. Cold detector loading is separated from warm inference; mBERT also records its internal model-copy/hash/session time. These are emulator measurements, not phone measurements. Sequential execution, OS/cache effects and one timing session limit performance comparisons. [Common-session conditions and results](expanded-four-model-benchmark-20261005.json).','',
        '## Local APKs','',
        'All are under `deliverables/expanded-20261005/` and excluded from public Git. Debug signatures are for local demonstration. The four algorithm variants coexist as `ph.smishguard.lr`, `.nb`, `.svm` and `.mbert`; installing a new model variant replaces that same algorithm on the emulator, while preserved old APKs allow rollback.','',
        '| Model | APK filename | SHA-256 |','|---|---|---|']
    for n in NAMES:lines.append(f'| {TITLES[n]} | `{artifacts[n]["filename"]}` | `{artifacts[n]["sha256"]}` |')
    lines+=['','## Remaining human work','',
        '- Complete independent blinded label confirmation/adjudication, privacy review and semantic template review. The supplied review workbook exposes computer labels, so use a blinded copy for independent agreement measurement.','- Confirm the supplied broad phishing scope and adjudicate the 18 excluded job/loan phishing conflicts.','- Obtain specific use/origin/consent evidence only for the held GitHub/team records if they are to enter a future experiment. No renewed project authorization is needed.','- Collect a genuinely new prospective evaluation set and measure performance on physical phones before deployment claims.','',
        '[Frozen protocol](expanded-comparison-protocol-20261005.md) · [Reproduction](expanded-comparison-reproduction-20261005.md) · [Prior preserved report](four-model-comparison.md).']
    (DOCS/'four-model-comparison-20261005.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    slide=['# SmishGuard presentation comparison — 5 October 2026','',
        'Preliminary retrospective evaluation: 3,340 source-supported records; identical 448-record test; source/rule labels awaiting independent confirmation.','',
        '| Algorithm | Phishing precision | Recall | F1 | Accuracy | Warm median (emulator) | APK size | Status |','|---|---:|---:|---:|---:|---:|---:|---|']
    for n in NAMES:
        r=results[n];slide.append(f'| {TITLES[n]} | {pct(r["precision"])}% | {pct(r["recall"])}% | {pct(r["f1"])}% | {pct(r["accuracy"])}% | {benchmark["results"][n]["p50_ms"]:.3f} ms | {artifacts[n]["apk_bytes"]/1e6:.2f} MB | trained, evaluated, APK verified |')
    slide+=['','Use “Model score,” not a validated probability. Report abstention separately. Most records have historical exposure; old/new scores cannot alone show improvement. Emulator timing is not physical-phone timing. mBERT is full float32 multilingual BERT.','',
        '[Full results, limitations and APK hashes](four-model-comparison-20261005.md) · [Machine-readable metrics](expanded-four-model-results-20261005.json) · [Verification](expanded-four-model-verification-20261005.json) · [Benchmark conditions](expanded-four-model-benchmark-20261005.json).',
        '', 'Actual fictional-message screenshots: local `deliverables/expanded-20261005/screenshots/`. Show the same English phishing example and benign Taglish example in all four apps; retain any false positives or negatives.']
    (DOCS/'four-model-presentation-20261005.md').write_text('\n'.join(slide)+'\n',encoding='utf-8')
    print('Aggregate reports generated without private messages, IDs or fitted weights.')

if __name__=='__main__':main()
