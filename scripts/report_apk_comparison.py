"""Publish sanitized aggregate findings for the frozen APK comparison."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import compare_frozen_apks as c


def report(run):
    run = Path(run)
    seal = c.n.load(run/'freeze.json')
    assert seal['inputs'] == c.verify_inputs()
    assert seal['cohort_sha256'] == c.n.digest(run/'cohort.json')
    assert seal['audit_sha256'] == c.n.digest(run/'cohort-audit.json')
    results = c.n.load(run/'results.json')
    assert results['freeze_sha256'] == c.n.digest(run/'freeze.json')
    rows = c.n.load(c.NEW/'dataset.json')
    ledger = c.n.load(run/'private-predictions.json')
    # Independent cohort membership and confusion reconstruction from original splits.
    old = c.n.load(c.OLD/'dataset.json'); split = c.n.load(c.OLD/'splits.json')['partitions']['grouped']
    nb_fold = c.n.load(c.NEW/'folds.json')['folds'][0]
    svm_exposed = {old[i]['id'] for part in ('train','validation') for i in split[part]}
    nb_exposed = {rows[i]['id'] for i in nb_fold['train']}
    cohort = c.n.load(run/'cohort.json')
    assert not {r['id'] for r in cohort} & (svm_exposed | nb_exposed)
    assert all(rows[r['index']]['label'] == r['label'] and rows[r['index']]['id'] == r['id'] for r in cohort)
    for model in ledger['records']:
        expected = results['models'][model['model']]['confusion']
        counts = dict(tn=0,fp=0,fn=0,tp=0)
        for record, score, prediction in zip(cohort,model['scores'],model['predictions']):
            assert prediction == int(score >= seal['models'][model['model']]['threshold'])
            counts[['tn','fp','fn','tp'][2*record['label']+prediction]] += 1
        assert counts == expected
    output = ROOT/'docs/apk-model-comparison-20261020'
    output.mkdir(exist_ok=True)
    c.n.save(output/'results.json', results)
    c.n.save(output/'identity-and-verification.json',dict(models=seal['models'],inputs=seal['inputs'],
        freeze_sha256=c.n.digest(run/'freeze.json'), results_sha256=c.n.digest(run/'results.json'),
        confusion_tables_recomputed=True,row_exposure_check_passed=True,
        inference_parity=results['inference_parity'],no_refitting=True,no_apk_changes=True))
    def pct(value):return f'{100*value:.2f}%'
    svm,nb = results['models']['svm'],results['models']['nb']
    lines=['# Linear SVM APK versus retrained Naive Bayes APK — 20 October 2026','',
        '**SVM leads the tiny matched check by one message; an unbiased overall winner cannot be established.** The user has no new separate labeled test set. This report compares the exact fitted classifiers in the two APKs, without training, tuning or modifying either app.','',
        'The original SVM uses 1,540 training / 516 validation / 498 test records (approximately 60/20/20). The new NB uses 2,734 training / 684 test records (80/20). Their original test sets and training pools differ, so their published accuracies cannot be ranked as a controlled comparison.','',
        '## Same-message comparison','',
        'I verified the APK model/adapter hashes, original fitting/split hashes, and the raw-to-masked lineage and matching labels for all 2,554 SVM corpus records. The two original tests share 72 record IDs, but intersection alone does not remove exposure to related messages. Starting from the fixed NB test, I removed any record or conservative component used in NB training or SVM training/validation. Components combine both saved grouping systems and exact casefolded raw/masked-text links. The retained IDs were frozen before matched-cohort prediction.','',
        '**Only 11 messages remain: nine inherited-label smishing and two legitimate messages, in ten components across three existing sources.** Zero retained components touch either model\'s fitting/tuning data under these checks. The tiny, skewed subset is not a representative real-traffic sample.','',
        '| Same 11 messages | Linear SVM | Naive Bayes |','|---|---:|---:|',
        f'| Accuracy | {pct(svm["accuracy"])} (9/11) | {pct(nb["accuracy"])} (8/11) |',
        f'| Smishing precision | {pct(svm["precision"])} | {pct(nb["precision"])} |',
        f'| Smishing recall | {pct(svm["recall"])} (7/9) | {pct(nb["recall"])} (6/9) |',
        f'| Smishing F1 | {pct(svm["f1"])} | {pct(nb["f1"])} |',
        f'| Balanced accuracy | {pct(svm["balanced_accuracy"])} | {pct(nb["balanced_accuracy"])} |',
        '| False alarms among legitimate messages | 0/2 | 0/2 |','| Missed scams | 2/9 | 3/9 |','',
        'Both classifiers get the same eight messages right and the same two scams wrong. SVM alone gets one additional scam right; NB alone gets none. Zero false alarms among only two legitimate messages gives very little evidence about real-world false-positive rates. As post-hoc context, calling every message smishing would also get 9/11 accuracy and 90% F1 on this skewed subset, while falsely flagging both legitimate messages. Accuracy/F1 on this sample cannot justify deployment claims.','',
        'Twenty thousand paired whole-component bootstrap draws give a conditional 95% percentile interval for NB-minus-SVM F1 of **−30.0 to 0.0 percentage points**, with observed difference −7.5 points. It includes no difference. This interval covers only resampling these ten components; it does not remove historical exposure, inherited-label uncertainty, model selection bias or source bias.','',
        '## What can be concluded','',
        'SVM has the better observed result on this very limited check. **Neither model is proven better by an unbiased benchmark.** The apparent advantage is one message. A larger training fraction alone does not establish that NB is better, and the earlier 99% scores do not settle this question.','',
        'For an unbiased comparison of the existing APK models, both frozen classifiers need the same independent, labeled messages, with campaign/template overlap removed from both models\' training and tuning records, representative language/source/class coverage, and labels decided without seeing model output. If old data must be reused, a new shared nested group evaluation can compare training procedures; it would not be an unbiased evaluation of these already fitted APK artifacts. No new retraining was performed for this report.','',
        '## Verification and scope','',
        'The APK JSON inference replay matches all 498 original SVM test scores (maximum error 2.23e-16) and all 684 original NB test scores (maximum error 7.89e-15), including threshold decisions. These original sets are used to verify model identity/inference, not to rank the models. Confusion counts were independently reconstructed from saved predictions. The [frozen protocol](../apk-model-comparison-20261020-protocol.md), [aggregate results](results.json) and [identity checks](identity-and-verification.json) accompany the report. Raw messages, IDs and per-message scores remain private under `research/runs/apk-comparison-20261020/run-v1/`.','',
        'The app\'s visible risk score combines classifier output with other evidence rules and includes abstention; these are classifier metrics, not end-to-end UI/notification accuracy or prospective phone measurements. Existing Android/Python parity checks establish inference compatibility, not detection generalization.','']
    (output/'FINDINGS.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Verified and saved',output/'FINDINGS.md')


if __name__=='__main__':report(sys.argv[1])
