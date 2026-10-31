"""Build the standalone/Colab notebook; embed audited code without private data."""
from pathlib import Path
import inspect
import nbformat as nbf
from smishguard import retraining as r
from smishguard import bantaytext_workflow as w
from smishguard import convert_supplied as c

ROOT=Path(__file__).resolve().parents[1]


def main():
    source=Path(r.__file__).read_text(encoding='utf-8')
    helpers='\nfrom difflib import SequenceMatcher\nURL = re.compile(r"https?://\\S+|www\\.\\S+", re.I)\n'
    helpers+='\n'+inspect.getsource(w.template_key)+'\n'+inspect.getsource(w.make_groups)
    helpers+='\n'+inspect.getsource(c.ranges)+'\n'+inspect.getsource(c.unicode_contract)
    embedded=source.replace('from .bantaytext_workflow import make_groups\nfrom .convert_supplied import unicode_contract\n',helpers)
    cells=[]
    def md(text):cells.append(nbf.v4.new_markdown_cell(text))
    def code(text):cells.append(nbf.v4.new_code_cell(text))
    md('''# Model Training and Evaluation — SmishGuard / Veritxt

Reproducible A–E comparison on the existing private inherited-label corpus. Keep
the established SmishGuard notebook unchanged. **All present results are
retrospective.** Re-splitting historically exposed SMS cannot create an untouched
test. No production model is replaced. Do not distribute data, fitted vocabulary,
private predictions or model coefficients without a separate rights/privacy review.

Synthetic probes are used only for software parity; all reported detection results
use the supplied corpus and its inherited labels. Independent target-task labels,
separate Tagalog/Taglish annotation and prospective SMS remain unresolved.
''')
    md('''## Setup

Use Python **3.12 / Unicode 15.0.0** for native Android export. From the repository:
`python -m pip install -r research/retraining-requirements.txt`. Colab can run this
notebook by itself: enable the next cell's install flag. No personal paths or
credentials are embedded. The full pipeline and grouping/export helpers are
included below; the repository is optional.
''')
    code('''import os, sys, subprocess
INSTALL_DEPENDENCIES = os.environ.get('SMISHGUARD_INSTALL', '0') == '1'
if INSTALL_DEPENDENCIES:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install',
        'numpy==2.2.6', 'scipy==1.15.3', 'scikit-learn==1.6.1',
        'joblib==1.6.0', 'threadpoolctl==3.7.0', 'cloudpickle==3.1.2',
        'matplotlib==3.10.7', 'pandas==2.3.3'])
print('Python:', sys.version.split()[0])
''')
    md('''## Configure explicit input and private versioned output

Set `SMISHGUARD_DATASET` or edit `DATASET_PATH`. CSV/JSON requires explicit `text`
(or `text_redacted`), `label` and preferably source/language/template metadata.
Accepted labels are ham/smishing or 0/1; generic spam is held for review. For a
Drive ZIP, set `MOUNT_DRIVE=True`, choose its path and set `ZIP_MEMBER` when there
are multiple eligible files. No automatic unrelated-file discovery occurs. ZIP
members are checked then read in memory; no scripts execute or arbitrary extraction.

The default uses the existing audited fitting view. This view is already masked;
it is not raw SMS. `REPLAY_EXISTING=True` verifies and displays a completed sealed
run without fitting, tuning, or re-evaluating its holdout. For a new run use a fresh
output directory and keep the default false. This adapter supports retrospective
inherited-label research; prospective reviewed data uses the repository's separate
intake protocol.
''')
    code('''from pathlib import Path
MOUNT_DRIVE = False
if MOUNT_DRIVE:
    from google.colab import drive
    drive.mount('/content/drive')
DATASET_PATH = Path(os.environ.get('SMISHGUARD_DATASET',
    'runs/bantaytext-20261013/notebook-run-v3/dataset.json'))
ZIP_MEMBER = os.environ.get('SMISHGUARD_ZIP_MEMBER') or None
OUTPUT_PATH = Path(os.environ.get('SMISHGUARD_RETRAIN_RUN',
    'runs/retraining-20261013/notebook-run-v1'))
REPLAY_EXISTING = os.environ.get('SMISHGUARD_REPLAY', '0') == '1'
SEED = 42
if not DATASET_PATH.is_file():
    raise FileNotFoundError('Set DATASET_PATH / SMISHGUARD_DATASET to your authorized private CSV/JSON/ZIP. No fallback dataset is used.')
''')
    md('''## Audited implementation

Only whitespace is collapsed. Raw text/original labels remain in the private
ledger. Exact conflicting labels and malformed/flagged records are held. The
label-blind near-template heuristic combines known template metadata with normalized
SequenceMatcher components at 0.85; Unicode casefold exact matches are also grouped.
Source-scoped campaign/sender/conversation groups are included if provided.

Twenty stratified group folds allocate 14/3/3, targeting 70/15/15. Actual counts
can differ. Every partition must have both classes and no group overlap; infeasible
splits fail, with no seed search or random fallback. Source-held-out stress tests
remain separate because three whole sources cannot represent a 70/15/15 split.
Chronological evaluation requires verified receipt timestamps, currently absent.

Every calibration fold fits its own TF-IDF/classifier using outer training only;
OOF margins fit the sigmoid, followed by a final training-only classifier refit.
Compare raw versus calibrated modes. This can shift score scale and is not a
guarantee of calibrated probabilities under real-traffic prevalence.
''')
    code('PIPELINE_SOURCE = '+repr(embedded))
    code('''import importlib.util, hashlib
try:
    from smishguard import retraining as pipeline
except ModuleNotFoundError:
    support = OUTPUT_PATH.parent / '_notebook_support'
    support.mkdir(parents=True, exist_ok=True)
    module_path = support / ('pipeline-' + hashlib.sha256(PIPELINE_SOURCE.encode()).hexdigest()[:12] + '.py')
    if not module_path.exists():
        module_path.write_text(PIPELINE_SOURCE, encoding='utf-8')
    spec = importlib.util.spec_from_file_location('standalone_smishguard_retraining', module_path)
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)
print('Configured families:', sorted({s['family'] for s in pipeline.matrix()}))
print('Fit configurations:', len(pipeline.matrix()), 'each compared raw and sigmoid')
''')
    md('''## Fit and select using training / validation only

A: word TF-IDF + LR; B: word TF-IDF + Linear SVM; C: word (1,2) + char_wb (3,5)
TF-IDF + SVM; D: same features + LR; E: word TF-IDF + NB. Tune C/class weights,
min_df, feature limits, n-gram variant and NB alpha (0.03/0.1/0.3/1/3).
Original distribution is fitted first; no validation/test resampling or SMOTE.

Provisional validation operating goals: precision >=0.90, FPR <=0.02 and >=5 TP.
Maximize recall, then phishing F1, AP, smaller artifact. Fail infeasible candidates.
These are research goals, pending an agreed deployment requirement. All family
winners, thresholds and files are sealed before holdout evaluation. The historical
baseline replay is saved separately in the audit-v1 artifact when available.
''')
    code('''if REPLAY_EXISTING:
    pipeline.verify_freeze(DATASET_PATH, OUTPUT_PATH)
else:
    pipeline.train(DATASET_PATH, OUTPUT_PATH, history='previously_used',
                   member=ZIP_MEMBER, seed=SEED)
audit = pipeline.load(OUTPUT_PATH / 'data-audit.json')
print({k:audit[k] for k in ('input_records','eligible_records','unique_normalized_messages',
    'template_groups','exclusions','distributions','partitions','pairwise_group_overlap')})
selection = pipeline.load(OUTPUT_PATH / 'selection.json')
print('Selected research configuration:', selection['selected']['id'] if selection['selected'] else None)
print('Operating policy:', selection['policy'])
baseline = OUTPUT_PATH.parent / 'audit-v1/baseline-replay.json'
if baseline.is_file():
    print('Historical baseline replay:', [{ 'id':x['id'], 'F1':x['metrics']['f1'],
       'max_score_error':x['max_score_error']} for x in pipeline.load(baseline)])
else:
    print('Historical fitted baseline not supplied here; consult audit report. No baseline result invented.')
''')
    md('''## Locked holdout evaluation and comparison

Run only after selection is frozen. Present the available holdout as **historically
exposed retrospective data**. Fresh, genuinely untouched evaluation is unavailable.
Do not reselect from this table. Accuracy can be high for an all-ham predictor;
use phishing precision/recall/F1, macro F1, PR-AUC, AP, ROC-AUC and confusion counts.
PR-AUC here is trapezoidal; AP is separately recorded. Brier/reliability diagrams
apply only to LR/NB probabilities or fitted sigmoid estimates, never SVM margins.
''')
    code('''if not REPLAY_EXISTING:
    pipeline.evaluate(DATASET_PATH, OUTPUT_PATH)
import pandas as pd
results = pipeline.load(OUTPUT_PATH / 'holdout-results.json')
table = []
for family,item in results['results'].items():
    c=item['candidate'];m=item['holdout']
    table.append(dict(family=family, configuration=c['id'], threshold=c['threshold'],
        **{k:m[k] for k in ('accuracy','precision','recall','f1','macro_f1','pr_auc','average_precision','roc_auc','brier')},
        confusion=m['confusion'], train_seconds=c['training_seconds'], artifact_bytes=c['artifact_bytes'],
        host_single_p50_ms=item['latency']['host_single_p50_ms']))
display(pd.DataFrame(table))
print(results['interpretation'])
''')
    code('''from IPython.display import display, Image
for filename in ('coverage.png','confusion-and-comparison.png','precision-recall.png','reliability.png'):
    display(Image(filename=str(OUTPUT_PATH / filename)))
''')
    md('''## Language, subgroup, robustness and uncertainty limits

Read support before metrics. Source/category names do not provide independently
verified phishing or legitimate banking/OTP/conversation labels. Current metadata
merges Filipino/Taglish. Subgroups need >=20 rows and >=5 each class for two-class
metrics; this floor is not a power analysis. Missing categories require human
annotation. Surface robustness edits use validation SMS only, with changed-row
counts; spelling/Taglish substitutions assume preserved meaning and need review.
They are supplementary experiments, not genuine new collected SMS or adversarial
security guarantees. Source/link-only controls and frozen URL removal probe shortcuts.

Repeated fitting seeds keep membership, configuration and threshold unchanged.
Cluster bootstrap intervals condition on fixed fitted predictions and exclude
selection, labels, historical exposure and fitting uncertainty.
''')
    code('''print('Selected subgroup diagnostics:', pipeline.load(OUTPUT_PATH/'subgroups-validation.json'))
print('Controlled validation robustness:', pipeline.load(OUTPUT_PATH/'robustness-validation.json'))
print('Shortcut controls:', pipeline.load(OUTPUT_PATH/'shortcut-validation.json'))
print('Source-transfer development stress:', pipeline.load(OUTPUT_PATH/'source-transfer-validation.json'))
print('Fitting seed variation:', selection['seed_variability'])
''')
    md('''## Offline export, provenance and remaining work

`candidate-model.json` includes ordered vocabulary/IDF/coefficients, independent
word/character block normalization, frozen Python Unicode tables, class order,
threshold and calibration. Android `ResearchLinearScorer` supports this contract;
the production ModelLoader/pointer remain unchanged. Python cases compare sparse
features, scores and threshold decisions at 1e-10 tolerance. JVM checks and optional
instrumentation use this actual export, not a pickle. Runtime applies abstention
for empty/unknown messages and rejects malformed/oversized inputs; report coverage
on real traffic separately from forced mathematical classifier performance.

XLM-R is not trained in the supplied environment: PyTorch/Transformers and a pinned
checkpoint are absent. The existing mBERT experiment is a different family. A future
XLM-R experiment must reuse exact eligible records/splits, use native tokenizer on
original authorized text, document pinned checkpoint/software/resources, compare
ordinary/weighted loss and freeze selection before prospective evaluation.
Masked classical results do not form a fair original-text transformer comparison.

Source attribution/terms and unresolved acquisition/privacy/label review remain in
`docs/source-evidence.md`. No personal/social input is added. Fitted artifacts remain
private; no redistribution or thesis clearance is inferred from public accessibility.

Method references: [TF-IDF 1.6](https://scikit-learn.org/1.6/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html),
[calibration](https://scikit-learn.org/stable/modules/calibration.html),
[XLM-R paper](https://arxiv.org/abs/1911.02116),
[checkpoint provenance](https://huggingface.co/FacebookAI/xlm-roberta-base).
''')
    code('''print('Environment and transformer status:', pipeline.load(OUTPUT_PATH/'environment.json'))
print('Saved artifact inventory:', sorted(p.name for p in OUTPUT_PATH.iterdir()))
PARITY_PATH = Path(os.environ.get('SMISHGUARD_PARITY',
    str(OUTPUT_PATH.parent / ('parity-' + selection['selected']['family'] + '-v2'))))
for kind in ('jvm','android'):
    parity=PARITY_PATH / ('research-' + kind + '-parity.json')
    print('Actual '+kind+' parity:', pipeline.load(parity) if parity.exists() else 'Not supplied; run repository parity commands.')
''')
    notebook=nbf.v4.new_notebook(cells=cells,metadata=dict(kernelspec=dict(name='python3',display_name='Python 3',language='python')))
    nbf.validate(notebook);nbf.write(notebook,ROOT/'research/Model_Training_and_Evaluation.ipynb')
    print('Notebook created with embedded audited source and no private SMS')


if __name__=='__main__':main()
