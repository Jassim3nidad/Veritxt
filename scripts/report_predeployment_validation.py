"""Publish actual aggregate further-validation evidence, including explicit release blockers."""
import argparse
from collections import Counter
import json
from pathlib import Path
import pickle
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from smishguard import bantaytext_workflow as w


def report(run):
    a=w.load(run/'aggregate.json');jvm=w.load(run/'parity/selected-jvm-aggregate.json');emu=w.load(run/'emulator-results.json')
    assert emu['status']=='passed' and jvm['maximum_score_error']<=1e-10
    assert emu['selected_candidate']['maximum_score_error']<=1e-10
    exported=w.load(run/'export-summary.json')
    assert w.digest(run/'parity/selected-model.json')==exported['model_sha256']
    assert w.digest(run/'parity/selected-cases.json')==exported['cases_sha256']
    original=w.load(ROOT/'docs/bantaytext-input-audit-20261013.json')
    for path,sha in original['protected_hashes'].items():assert w.digest(ROOT/path)==sha
    tests=Counter()
    for path in (ROOT/'android/app/build/test-results/testDevelopmentUnitTest').glob('TEST-*.xml'):
        xml=ET.parse(path).getroot()
        for key in ('tests','failures','errors','skipped'):tests[key]+=int(xml.get(key,'0'))
    assert not tests['failures'] and not tests['errors']
    apk=ROOT/'android/app/build/outputs/apk/development/app-development.apk'
    with zipfile.ZipFile(apk) as z:
        assert 'assets/selected-svm-model.json' not in z.namelist() and 'assets/selected-svm-cases.json' not in z.namelist()
        assert z.read('assets/model.json')==(ROOT/'android/app/src/development/assets/model.json').read_bytes()
        for name in z.namelist():
            if name.endswith('.dex'):
                dex=z.read(name)
                assert b'Lph/smishguard/SelectedSvmScorer;' not in dex
    # Independently recompute every new outer-source confusion matrix.
    source_cases=0
    for source,entries in a['nested_source'].items():
        parts=w.load(run/'source-heldout'/source/'partitions.json')
        assert not set(parts['test']) & (set(parts['train'])|set(parts['validation']))
        for algorithm,result in entries.items():
            folder=run/'source-heldout'/source
            freeze=w.load(folder/(algorithm+'-freeze.json'))
            assert w.digest(folder/(algorithm+'-pipeline.pkl'))==freeze['pipeline_sha256']
            pred=w.load(folder/(algorithm+'-predictions.json'))
            assert pred['indices']==parts['test']
            assert w.calculate_metrics(pred['labels'],pred['scores'],freeze['threshold'])==result['test_metrics']
            source_cases+=1
    privacy= w.load(run/'privacy-emulator-results.json') if (run/'privacy-emulator-results.json').exists() else None
    if privacy is not None:assert privacy['status']=='passed'
    a.update(jvm=jvm,emulator={k:v for k,v in emu.items() if k!='instrumentation'},
        privacy_emulator=privacy,verification=dict(recomputed_source_runs=source_cases,protected_files_unchanged=len(original['protected_hashes']),
            junit=dict(tests),research_tests=117,build='assembleDevelopment + assembleDevelopmentAndroidTest + lintDevelopment + JVM passed',
            selected_scorer_excluded_from_production_apk=True,active_model_inside_apk_unchanged=True,
            apk_sha256=w.digest(apk),physical_device='Not tested'))
    w.save(ROOT/'docs/bantaytext-predeployment-validation-20261013.json',a)
    lines=['# Further SmishGuard predeployment validation — 13 October 2026','',
        'Latest clarification: inherited labels are permitted by the original task with explicit limitations; another independently human-labeled upload is not a blanket software gate. The user reports phone checks completed. Subsequent [raw-SMS validation](bantaytext-raw-sms-validation-20261013.md) addresses preprocessing; the following results preserve the earlier validation stage.', '',
        '**Release decision: keep the active model.** Further engineering checks passed, but predictive deployment validation remains incomplete. The user-supplied ZIP is byte-identical to the previously used October 12 package; there are zero completed independent labels and zero new prospective intake records. Source transfer still fails on the Tagalog corpus.','',
        '## Data identity and independent evidence','',
        f"ZIP SHA-256: `{a['snapshot']['archive_sha256']}`. All {a['snapshot']['members_verified']} original archive members match preserved intake hashes. The 3,340-record retrospective review has 0 finalized decisions; the package workbook also has no completed final labels. Do not treat source/rule labels as independent truth or rename previously used data as unseen validation.", '',
        'The [protocol](bantaytext-predeployment-protocol-20261013.md) was saved before additional predictions. The selected original SVM, its threshold ≥0.37, coefficients, vocabulary, calibration and previous split remain unchanged. No test result was used to tune that candidate. All populated artifacts stay private under `research/runs/bantaytext-20261013/validation-v2/`.','',
        '## Fixed-candidate uncertainty','',
        'Two thousand paired whole-template bootstrap draws use the fixed grouped-test candidate and standard SVM baseline on the same 498 records. These intervals do not include fitting, model selection, inherited-label uncertainty or source bias.','',
        '| Metric | 95% descriptive interval |','|---|---|']
    for key,value in a['confidence_intervals']['intervals'].items():lines.append(f"| {key} | {value['low']:.4f}–{value['high']:.4f} |")
    lines+=['','The grouped-test F1 remains 0.9524. The conditional interval is broad; observed gains over a standard baseline do not prove prospective deployment superiority.','',
        '## Stricter source-held-out operating points','',
        'Each outer source and every overlapping template group are excluded before fitting. Only its source complement supplies a 5-fold grouped inner train/validation split; SVM calibration uses 3-fold grouped OOF training margins. Thresholds are chosen using inner validation only and frozen before outer prediction. Algorithm settings remain historical fixed values (NB alpha=.1, LR/SVM C=10); prior corpus exposure/setting selection prevents an unbiased prospective claim.','',
        '| Held source | Algorithm | Threshold | Precision | Recall | F1 | TN/FP/FN/TP |','|---|---|---:|---:|---:|---:|---|']
    for source,entries in a['nested_source'].items():
        for algorithm,r in entries.items():
            m=r['test_metrics'];c=m['confusion'];lines.append(f"| {source} | {algorithm} | {r['threshold']:.2f} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} | {c['tn']}/{c['fp']}/{c['fn']}/{c['tp']} |")
    lines+=['','The selected algorithm family has Tagalog-held-out F1 **0.3896**, despite recalibrating its operating point entirely outside that source. This confirms a material source-generalization concern. BwandoWando has only positive labels, so FPR/ROC/AP there are not estimable. Source-specific confusion counts and partition supports are in [JSON](bantaytext-predeployment-validation-20261013.json).','',
        '## Targeted errors and calibration','',
        '| Original source category | Ham support | FP | Observed FPR | Wilson 95% interval |','|---|---:|---:|---:|---|']
    for category,r in a['targeted'].items():
        if 'ham' in r:
            ci=r['wilson_fpr'];lines.append(f"| {category} | {r['ham']} | {r['fp']} | {r['false_positive_rate']:.4f} | {ci['low']:.4f}–{ci['high']:.4f} |")
    lines+=['','Zero OTP errors in 55 records does not establish zero population FPR: its Wilson upper bound is about 6.53%. Wilson bounds do not cover grouping/selection/label uncertainty. No independently validated bank/e-wallet category is available. Broad notifications are not a bank-specific safety test.','',
        f"Grouped-test ECE is {a['calibration_reliability']['expected_calibration_error']:.5f}, Brier 0.01567 and log loss 0.06074 under inherited retrospective labels. The score transform was fitted; numerical calibration quality on real incoming financial SMS remains unverified. The native test scorer never marks its score as a validated probability.", '',
        '## Frozen-input robustness','',
        '| Transformation | Changed decisions /498 | Max absolute score change |','|---|---:|---:|']
    for name,r in a['robustness'].items():lines.append(f"| {name} | {r['changed_decisions']} | {r['maximum_absolute_score_change']:.5f} |")
    lines+=['','All scores stayed finite. Casing, whitespace and inter-token punctuation happened to preserve this cohort’s features. Inserting Taglish wording or removing link markers can alter content/features; changed decisions are stress diagnostics, not newly adjudicated errors. The current model cannot be fixed using these exposed test observations and then evaluated on that same test as an independent improvement.','',
        '## Actual SVM native compatibility and offline emulator','',
        'The selected SVM was exported into a test-only Unicode-15/English-stopword/bigram scorer. It preserves minimum two-codepoint tokens, removes stopwords before bigrams, retains unknown-token adjacency, ordered feature indices, IDF/raw counts/L2, coefficients, exactly one sigmoid and class/threshold mapping. These checks now apply to the actual selected SVM, rather than only the earlier portable LR comparator.','',
        f"Python/JVM and API36 offline emulator parity passed on **{exported['cases']} cases: {exported['real_masked_test_cases']} actual private masked test views plus {exported['synthetic_probes']} synthetic probes**. Maximum score difference is {jvm['maximum_score_error']:.3g}; maximum feature difference is {jvm['maximum_feature_error']:.3g}. Seven required empty/random/keyboard/placeholder/malformed inputs abstained; overlong input failed. Metadata, invalid numeric, class orientation and approval-field tampering were rejected.", '',
        'The contract expects already masked training views. A reviewed raw-SMS masking/integration contract remains necessary before release. The scorer lives only in test sources and is absent from the production APK. The production loader explicitly rejects its schema; no active inference path was switched. The development APK still contains byte-identical active weights and no selected-SVM model or private case asset. Test artifacts/APKs remain private.','']
    e=emu['selected_candidate']
    lines+=[f"Emulator-only measurements: JSON model {exported['model_bytes']:,} bytes / {exported['feature_count']:,} features; load {e['load_ms']:.1f} ms; mean score-path time {e['mean_score_ms']:.3f} ms/message. The score timing includes tokenization/features/dot product/sigmoid, excludes model load, JSON probe parsing and input-abstention checks. Whole instrumentation-process PSS went from {e['pss_kib_before']:,} to {e['pss_kib_after']:,} KiB; this includes test data/runtime and is not isolated model memory or phone benchmarking.", '',
        'Four offline Android instrumentation checks passed, covering the selected SVM, unchanged active model and synthetic sklearn exports. Airplane mode was enabled, Wi-Fi disabled and INTERNET permission denied. Original connectivity settings were restored. The emulator is verified using ro.kernel.qemu=1; no physical device was used.','']
    if privacy:
        lines+=['The existing complete development emulator suite also passed: UI/lifecycle/SMS decoding, denied/granted/blocked notification behavior, offline supplied exports, synthetic modem SMS, large-text accessibility and private-storage scanning. Receiver tests used fictional markers only; selected-model inference used already masked private test views directly inside the isolated test APK. No real SMS was sent through the receiver.','']
    lines+=[f"Verification: 117 research tests passed; JVM {tests['tests']-tests['skipped']} passed/{tests['skipped']} conditional skips/0 failures; Android assemble, test-APK assemble and lint passed. All {len(original['protected_hashes'])} protected app/model hashes remain unchanged. Initial harness attempts failed on Windows manifest path separators and absent shared comparator fixtures. The broader emulator run also exposed a stale UI-test assertion that warnings were disabled, contrary to the prior team-enabled original-model policy; CompactResultTest now checks the actual build policy. These corrections affect validation tooling/tests only. No production behavior changed. Failed attempts/logs remain private; no partial fit was selected.", '',
        '## Required next evidence','',
        'Supply a genuinely new, authorized cohort collected after a documented candidate freeze. Complete human privacy/source-use checks, blinded independent A/B labels and adjudication before predictions; reject historical exact/near-template overlap and freeze membership. The previous 3,340-row blinded packets can improve retrospective label quality but cannot turn those messages into prospective evidence. A new candidate-specific freeze is saved privately as `prospective-candidate-freeze.json`; the old four-model freeze is preserved.','',
        'Additional unseen or independently reviewed data would strengthen calibration/threshold and financial-message evidence; its absence limits claims rather than imposing a blanket permission gate. The later raw-input check and user-reported phone completion are documented separately. The measured source-transfer weakness remains the release concern. Active weights remain unchanged; nothing was deployed, committed, pushed or published.','',
        '## Changed files','',
        'Additional scripts: `research/smishguard/predeployment_validation.py`, `scripts/report_predeployment_validation.py`, `scripts/verify_selected_svm_emulator.py`; Python guards: `research/tests/test_predeployment_validation.py`. Test-only Kotlin scorer/parity: `android/app/src/softwareTest/java/ph/smishguard/SelectedSvmParity.kt`, JVM `SelectedSvmParityTest.kt` and instrumented `SelectedSvmAndroidTest.kt`. `CompactResultTest.kt` corrects the stale policy expectation. The protocol, this report/JSON, research README and candidate/contract documentation were updated. Existing notebook, fitted candidates, previous evaluation outputs, production sources and installed assets were preserved.','',
        '## Reproduction','',
        '```powershell',"$env:PYTHONPATH='research'","$env:PYTHONIOENCODING='utf-8'",
        "research/.venv/Scripts/python.exe -m smishguard.predeployment_validation research/runs/bantaytext-20261013/notebook-run-v3 '<authorized October 12 ZIP path>' research/runs/bantaytext-20261013/NEW-VALIDATION-RUN",
        "$parityPath=(Resolve-Path research/runs/bantaytext-20261013/NEW-VALIDATION-RUN/parity).Path",
        "$env:JAVA_TOOL_OPTIONS='-Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir'",
        '.\\gradlew.bat :app:testDevelopmentUnitTest :app:assembleDevelopment :app:assembleDevelopmentAndroidTest :app:lintDevelopment "-PmodelParityDir=$parityPath" -PinstrumentedBuild=development --console=plain',
        '# Start a designated API36 test emulator; no physical-device use.',
        "research/.venv/Scripts/python.exe scripts/verify_selected_svm_emulator.py --adb '<SDK platform-tools adb path>' --output research/runs/bantaytext-20261013/NEW-VALIDATION-RUN/emulator-results.json",
        '# Optional complete development regression suite, with SDK adb on PATH:',
        'research/.venv/Scripts/python.exe scripts/emulator_verify.py --variant development --output research/runs/bantaytext-20261013/NEW-VALIDATION-RUN/privacy-emulator-results.json',
        'research/.venv/Scripts/python.exe -m unittest discover -s research/tests -q',
        'research/.venv/Scripts/python.exe scripts/report_predeployment_validation.py research/runs/bantaytext-20261013/NEW-VALIDATION-RUN','```','']
    (ROOT/'docs/bantaytext-predeployment-validation-20261013.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Further validation report saved; deployment not approved')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);report(p.parse_args().run)
