"""Validation and label-blind template grouping. Read operation-reviewed, redacted data only."""
import csv
from datetime import datetime
from difflib import SequenceMatcher
from .preprocessing import normalize

def read_dataset(path, study_role="primary"):
    from .intake import read_csv, validate_record, eligible_category, TOKEN
    rows = read_csv(path, approved=True)
    for number, row in enumerate(rows, start=2):
        try:
            validate_record(row)
            category, reason = eligible_category(row, study_role)
            if reason or row["label"] != ("1" if category == "financial_phishing" else "0"):
                raise ValueError("Training requires eligible resolved labels; import reviewed intake first")
            if not TOKEN.fullmatch(row["approval_reference"]):
                raise ValueError("Missing intake review reference (legacy approval_reference column)")
        except ValueError as error:
            raise ValueError(f"CSV row {number}: {error}") from None
    return rows


def template_groups(rows, similarity=0.85):
    """Deterministic connected components of redacted character-template similarity.

    O(nÂ²), appropriate for this study's 1,200â€“2,500 target. No labels used.
    Caller records group membership and similarity policy, then manually audits templates.
    """
    texts = [normalize(r["text_redacted"]) for r in rows]
    parent = list(range(len(rows)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(rows)):
        for j in range(i):
            if (texts[i] == texts[j] or (rows[i].get("template_group") and
                    rows[i].get("template_group") == rows[j].get("template_group"))):
                parent[root(i)] = root(j)
                continue
            # Length upper bound makes obvious nonmatches inexpensive.
            if 2 * min(len(texts[i]), len(texts[j])) / max(1, len(texts[i])+len(texts[j])) < similarity:
                continue
            if texts[i] == texts[j] or SequenceMatcher(None, texts[i], texts[j], autojunk=False).ratio() >= similarity:
                parent[root(i)] = root(j)
    return [root(i) for i in range(len(rows))]

def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamps require a recorded timezone")
    return parsed

def split_rows(rows, groups, strategy, seed):
    import numpy as np
    from sklearn.model_selection import train_test_split, GroupShuffleSplit, StratifiedGroupKFold
    ids = np.arange(len(rows))
    y = np.array([int(r["label"]) for r in rows])
    if strategy in {"time", "time-group"}:
        dates = [timestamp(r.get("received_at", "")) for r in rows]
        ids = np.array(sorted(ids, key=lambda i: (dates[i], rows[i]["id"])))
        # Keep equal timestamps on one side; invalid/too-small splits are rejected below.
        boundaries = [dates[ids[int(len(ids)*fraction)]] for fraction in (.55, .70, .85)]
        partitions = [[i for i in ids if sum(dates[i] >= b for b in boundaries) == p] for p in range(4)]
    elif strategy == "random":
        train, held = train_test_split(ids, test_size=.45, random_state=seed, stratify=y)
        validation, held = train_test_split(held, test_size=2/3, random_state=seed, stratify=y[held])
        calibration, test = train_test_split(held, test_size=.5, random_state=seed, stratify=y[held])
        partitions = [train, validation, calibration, test]
    elif strategy == "group":
        groups = np.asarray(groups)
        def split(subset, fraction):
            a,b = next(GroupShuffleSplit(n_splits=1, test_size=fraction, random_state=seed).split(subset, groups=groups[subset]))
            return subset[a], subset[b]
        train, held = split(ids, .45)
        validation, held = split(held, 2/3)
        calibration, test = split(held, .5)
        partitions = [train, validation, calibration, test]
        # Fixed fold allocation targets 55/15/15/15 without searching favorable seeds.
        # SGKF approximates class balance while keeping every component indivisible.
        if len(np.unique(groups)) >= 20 and min(np.bincount(y, minlength=2)) >= 20:
            folds = [b for _, b in StratifiedGroupKFold(n_splits=20, shuffle=True,
                     random_state=seed).split(ids, y, groups)]
            partitions = [np.concatenate(folds[a:b]) for a,b in ((0,11),(11,14),(14,17),(17,20))]
    else:
        raise ValueError("Unknown split strategy")
    excluded = []
    if strategy == "time-group":
        memberships = {}
        for part, indices in enumerate(partitions):
            for i in indices: memberships.setdefault(groups[i], set()).add(part)
        crossing = {g for g, parts in memberships.items() if len(parts) > 1}
        excluded = [int(i) for i in ids if groups[i] in crossing]
        partitions = [[i for i in part if groups[i] not in crossing] for part in partitions]
    result = dict(zip(("train", "validation", "calibration", "test"), [[int(i) for i in p] for p in partitions]))
    if any(len({rows[i]["label"] for i in p}) != 2 for p in result.values()):
        raise ValueError("Each partition requires both classes; report this split as not viable, do not retry seeds until favorable")
    if excluded: result["excluded"] = excluded
    return result
