"""Build a self-contained Colab notebook; never executes the supplied ZIP scripts."""
from pathlib import Path
import json
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]


def main():
    nb = nbf.v4.new_notebook(); cells = []
    def md(s): cells.append(nbf.v4.new_markdown_cell(s))
    def code(s): cells.append(nbf.v4.new_code_cell(s))
    md('''# SmishGuard: baseline versus proposed Multinomial Naive Bayes

Execute top to bottom in Python 3.12 (Google Colab or the local research environment).
The complete implementation is embedded below; no repository checkout is needed in Colab.
Only the configuration cell needs changing for another input/output location.

This is **retrospective research**: the October 12 corpus has already influenced
earlier models. A new split cannot create independent prospective evidence.
Source/rule labels are inherited, not independently verified. Keep all message-bearing
files and fitted vocabulary private. The notebook displays aggregate results only.
Production assets and existing notebooks are preserved.

Before fitting, the fixed selection rule is maximum validation scam F1, then recall,
precision, smaller classifier file, configuration ID. No threshold tuning, resampling,
feature selection from held-out data, or refitting on validation. Default NB threshold
is >=0.5; SVM margin threshold is >=0. No claim of calibrated fraud probability.
''')
    md('''## 1. Environment and configuration

The default Drive ZIP is `/content/drive/MyDrive/datasets/smishguard_dataset_2026-10-12.zip`.
Drive mounts only in Colab when needed. Set `SMISHGUARD_NB_DATASET` and
`SMISHGUARD_NB_OUTPUT` to configure paths without changing intermediate cells.
Each execution requires a **new** output directory; completed evidence is never overwritten.
Google Colab execution itself has not been tested by running in a remote Colab account;
the same notebook is executed locally with the pinned packages.
''')
    code('''import os, sys, subprocess, importlib.util
from pathlib import Path
try:
    IN_COLAB = importlib.util.find_spec('google.colab') is not None
except ModuleNotFoundError:
    IN_COLAB = False
PINS = ['numpy==2.2.6','scipy==1.15.3','scikit-learn==1.6.1','pandas==2.3.3',
        'matplotlib==3.10.7','joblib==1.6.0','threadpoolctl==3.7.0']
if IN_COLAB:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', *PINS])
from datetime import datetime, timezone
STAMP = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
if IN_COLAB:
    default_zip = Path('/content/drive/MyDrive/datasets/smishguard_dataset_2026-10-12.zip')
    default_output = Path('/content/drive/MyDrive/smishguard-results') / ('nb-comparison-' + STAMP)
else:
    root = Path.cwd() if (Path.cwd()/'research').is_dir() else Path.cwd().parent
    default_zip = root/'research/data/newdata-20261013/smishguard_dataset_2026-10-12.zip'
    default_output = root/'research/runs/nb-comparison-20261016'/STAMP
DATASET_PATH = Path(os.environ.get('SMISHGUARD_NB_DATASET', str(default_zip))).expanduser().resolve()
OUTPUT_PATH = Path(os.environ.get('SMISHGUARD_NB_OUTPUT', str(default_output))).expanduser().resolve()
ZIP_MEMBER = os.environ.get('SMISHGUARD_NB_MEMBER', 'smishguard_dataset_2026-10-12/smishguard_dataset.csv')
if IN_COLAB and ('/content/drive/' in str(DATASET_PATH) or '/content/drive/' in str(OUTPUT_PATH)):
    from google.colab import drive
    drive.mount('/content/drive')
if not DATASET_PATH.is_file():
    raise FileNotFoundError(f'Dataset ZIP missing: {DATASET_PATH}. Configure SMISHGUARD_NB_DATASET or DATASET_PATH.')
print('Python:', sys.version)
print('Dataset:', DATASET_PATH.name, '| Output:', OUTPUT_PATH)
''')
    md('''## 2. Complete audited implementation

The CSV schema is inspected explicitly. Only `smishguard_dataset.csv` is extracted
into memory; `asea_ready.csv` is an overlapping auxiliary copy and the ZIP's scripts
are never run. The third label `gambling_ad` is held, with no invented binary mapping.
Flagged records and normalized label conflicts are held. Exact/casefold/whitespace
duplicates are removed **before** splitting, retaining first eligible occurrence.

The existing three-source research scope is retained. Pending GitHub and team
permission/consent rows remain held. The source ledger and inherited labels stay
private; this is not a source-license or label-quality certification.

Text normalization collapses whitespace only, followed by Unicode lowercase.
The shared tokenizer preserves whole HTTP(S)/www URLs (including attached terminal
punctuation), currency amounts, decimal/grouped numbers and one-character words.
No URL/amount masking, translation, stemming or accent removal is added.
Both approaches remove the same conservative fixed English list, avoiding the full
English list's Filipino collisions such as `at`, `may`, `an`, and retaining negations.
No automatic language detection or Tagalog stopword removal is used.

All models use TF-IDF (1,2), raw TF, smoothed IDF, L2 normalization, min_df=1 and
max_features=None. A: NB alpha=1.0; B: NB alpha=0.1. Additional NB alpha=.01/.5/2
and LinearSVC C=1 use the same features. This isolates alpha for the NB comparison.
''')
    source = (ROOT/'research/smishguard/nb_comparison.py').read_text(encoding='utf-8')
    code('''import importlib.util, tempfile
IMPLEMENTATION_SOURCE = '''+repr(source)+'''
implementation_dir = Path(tempfile.mkdtemp(prefix='smishguard-nb-'))
implementation_file = implementation_dir/'nb_comparison.py'
implementation_file.write_text(IMPLEMENTATION_SOURCE, encoding='utf-8')
spec = importlib.util.spec_from_file_location('smishguard_nb_notebook', implementation_file)
experiment = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = experiment
spec.loader.exec_module(experiment)
print('Embedded implementation SHA-256:', experiment.digest(implementation_file))
print('Stopwords:', experiment.STOP_WORDS)
print('Selection policy:', experiment.POLICY)
''')
    md('''## 3. Cleaning, grouping, fitting and validation-only selection

Label-blind connected components combine supplied templates, source-scoped sender
metadata, and Unicode template similarity >=.85 after URL/number removal **for grouping
only**. Near matches with mixed labels are retained together and queued for review;
similarity alone does not prove a label error. Campaign identities may be incomplete.
Twenty stratified group folds, seed 42, are allocated 14/3/3 for approximately
70/15/15. Indivisible groups can shift prevalence and size; no seed search is used.
All group and normalized-text overlaps must be zero. Vocabulary and IDF fit training
only, separately for each model. Test text is not transformed until selection is sealed.
''')
    code('''import pandas as pd
audit = experiment.train(DATASET_PATH, OUTPUT_PATH, ZIP_MEMBER)
display(pd.DataFrame([audit['input_labels']], index=['before cleaning']))
display(pd.DataFrame([audit['after_cleaning']], index=['after cleaning']))
display(pd.DataFrame(audit['partitions']).T)
print('Missing:', audit['missing'])
print('Exclusions (reasons may overlap):', audit['exclusion_reason_counts'])
print('Raw exact duplicates:', audit['raw_exact_duplicate_extra_rows'],
      '| normalized extra rows:', audit['normalized_duplicate_extra_rows'],
      '| conflicting groups:', audit['conflicting_normalized_groups'])
print('Groups:', audit['groups'], '| mixed-label template groups:', audit['mixed_label_template_groups'])
print('Group overlaps:', audit['group_overlap'], '| text overlaps:', audit['normalized_text_overlap'])
display(pd.DataFrame({'before':audit['language_before'],'after':audit['language_after']}))
display(pd.read_csv(OUTPUT_PATH/'hyperparameters.csv'))
selection = experiment.load(OUTPUT_PATH/'selection.json')
print('Frozen research selection:', selection['selected'], '| best NB:', selection['best_nb'])
''')
    md('''## 4. One locked retrospective test evaluation

Evaluate A, B, SVM and the validation-selected best NB (unique configurations only).
Changing selection, data, code or artifacts invalidates the freeze. An exclusive
marker refuses a second/interrupted test evaluation. These safeguards apply to this
run; historical exposure of the corpus remains. Do not revise the winner after
viewing the test table. Confusion matrices use rows=actual, columns=predicted,
ham=0 and scam=1. FPR=FP/(TN+FP); FNR=FN/(FN+TP).
''')
    code('''experiment.evaluate(DATASET_PATH, OUTPUT_PATH)
experiment.plots(OUTPUT_PATH)
table = pd.read_csv(OUTPUT_PATH/'comparison.csv')
display(table)
results = experiment.load(OUTPUT_PATH/'test-results.json')
for result in results['results']:
    print(result['spec']['id'], 'class-level report')
    display(pd.DataFrame(result['test']['classification_report']).T)
    print('Language metadata:', result['language'])
from IPython.display import Image, display
display(Image(filename=str(OUTPUT_PATH/'confusion-matrices.png')))
display(Image(filename=str(OUTPUT_PATH/'comparison.png')))
''')
    md('''## 5. Offline inference evidence and Android compatibility

Save classifier and vectorizer pickles, exact preprocessing configuration, metadata,
split/cleaning ledgers, validation/test predictions and a separate schema-8 JSON
candidate. JSON reference inference independently reconstructs TF-IDF features and
scores for frozen test messages and synthetic English, Tagalog, Taglish, URL, numeric,
short, random and financial-scam probes. These probes have no measured research labels.
Pickles must only be loaded from this trusted run.

An all-unknown vector returns NB's class prior (or SVM's intercept), which is not
fraud evidence. The diagnostic wrapper abstains for zero-feature input; benchmark
classification metrics above retain the unmodified model decision. Other recognizable
random fragments can still receive high scores. Scores are **uncalibrated**, including
NB posteriors. The diagnostic abstention policy is not a validated production policy.

The Android ModelLoader currently supports different schema/tokenization contracts.
Its scorers split URLs/amounts and use at least two word characters; its masking
adapter also changes these raw inputs. Schema 8 is deliberately separate and marked
android_compatible=false. A matching Kotlin tokenizer/TF-IDF/linear scorer and actual
JVM/device parity are required before deployment. Python JSON parity is not Android
parity. No app model, warning behavior, asset or production pointer is changed.
''')
    code('''for result in results['results']:
    name = result['spec']['id']
    checks = experiment.load(OUTPUT_PATH/name/'inference-checks.json')
    print(name, {k:v for k,v in checks.items() if k != 'probes'})
    display(pd.DataFrame(checks['probes'][:15]).drop(columns=['text']))
print('Reproducibility metadata:', experiment.load(OUTPUT_PATH/'metadata.json'))
print('Artifacts saved to:', OUTPUT_PATH)
experiment.verify_freeze(DATASET_PATH, OUTPUT_PATH)
print('Training and selection freeze reverified.')
''')
    md('''## 6. Interpretation, limits and reproduction

Compare scam precision/recall/F1 and macro-F1, not accuracy alone. FN means a missed
scam; FP interrupts a legitimate message. The prespecified F1 selection rule gives
neither mistake an explicit deployment cost. Do not call alpha=.1 superior unless
both validation and retrospective test evidence support the bounded claim; no
statistical significance is established by a point estimate.

This corpus's rule-derived labels, historical exposure, source imbalance, heuristic
templates, unknown true campaign boundaries, and unverified receipt timestamps limit
generalization. Financial scams are included but no independently adjudicated financial
subset is available. Metadata combines Filipino/Taglish, so separate Tagalog and Taglish
metrics are unavailable. Small subgroup support cannot establish language robustness.
The 500 gambling_ad records are excluded, limiting conclusions for that traffic.
Source-held-out and prospective independent evaluation remain future confirmation.

Local reproduction: install `research/nb-comparison-requirements.txt`, then
`research/.venv/Scripts/python.exe scripts/execute_nb_comparison_notebook.py --output research/runs/nb-comparison-20261016/NEW-RUN`.
In Colab upload this notebook, configure the ZIP/output paths above, and Run all.
All tables come from execution; no expected or fabricated performance is included.

Method references: [TF-IDF](https://scikit-learn.org/1.6/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html),
[MultinomialNB](https://scikit-learn.org/1.6/modules/generated/sklearn.naive_bayes.MultinomialNB.html),
[StratifiedGroupKFold](https://scikit-learn.org/1.6/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html).
''')
    nb.cells = cells
    nb.metadata.kernelspec = dict(name='python3', display_name='Python 3', language='python')
    nbf.validate(nb)
    path = ROOT/'research/NB_Baseline_Proposed_Comparison.ipynb'
    nbf.write(nb, path); print(path)


if __name__ == '__main__': main()
