"""Software-only checks; these do not create research models or research results."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from smishguard import fair_compare as fair


class FairComparisonTests(unittest.TestCase):
    def test_existing_python_golden_fixtures_without_training(self):
        from smishguard.parity import predict
        root = Path(__file__).resolve().parents[2] / "android/app/src/androidTest/assets/software"
        for name in fair.NAMES:
            model = json.loads((root / f"{name}-model.json").read_text(encoding="utf-8"))
            for case in json.loads((root / f"{name}-cases.json").read_text(encoding="utf-8")):
                score, label = predict(model, case["text"])
                self.assertAlmostEqual(score, case["score"], places=10)
                self.assertEqual(label, case["suspicious"])

    def test_inner_groups_are_shared_and_isolated(self):
        y = np.array([0, 1] * 30)
        groups = np.repeat(np.arange(30), 2)
        folds = fair.training_folds(y, groups)
        self.assertEqual(len(folds), 5)
        seen = []
        for train, valid in folds:
            self.assertFalse(set(groups[train]) & set(groups[valid]))
            seen.extend(valid)
        self.assertEqual(sorted(seen), list(range(60)))

    def test_nonviable_folds_and_small_sample_rejected(self):
        with self.assertRaises(ValueError):
            fair.training_folds(np.zeros(30), np.arange(30))
        with patch.object(fair, "read_dataset", return_value=[]):
            with self.assertRaisesRegex(ValueError, "1,200"):
                fair.prepare(Path("unused"), Path("unused"), "previously_used", Path("unused"))

    def test_equal_grid_and_algorithm_identity(self):
        self.assertEqual(len(fair.GRID), 3)
        for name in fair.NAMES:
            for value in fair.GRID:
                model = fair.classifier(name, value)
                self.assertEqual(getattr(model, "alpha" if name == "nb" else "C"), value)
        with self.assertRaises(ValueError):
            fair.classifier("forest", 1)

    def test_test_set_cannot_be_opened_after_artifact_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "fixture.csv"
            dataset.write_text("SOFTWARE ONLY")
            (root / "model.json").write_text("changed")
            (root / "freeze.json").write_text(json.dumps(dict(dataset_sha256=fair.digest(dataset),
                protocol_sha256=fair.digest(fair.PROTOCOL), files={"model.json": "wrong"})))
            with patch.object(fair, "read_dataset", side_effect=AssertionError("Test data accessed")):
                with self.assertRaisesRegex(ValueError, "artifact changed"):
                    fair.evaluate(dataset, root)

    def test_small_group_uncertainty_suppressed(self):
        result = fair.paired_f1_intervals(np.array([0, 1]), {}, np.array([0, 1]))
        self.assertIsNone(result["intervals"])


if __name__ == "__main__":
    unittest.main()
