"""Cache recovery must reject fitted-source changes and post-selection work."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import recover_update_mbert_cache as recovery
from smishguard.train import write_json


class CacheRecoveryBoundaries(unittest.TestCase):
    def test_recovery_forbidden_after_selection_or_test_opening(self):
        for marker in ('selection.json','test-started.json'):
            with tempfile.TemporaryDirectory() as directory:
                run=Path(directory)/'run';run.mkdir()
                (run/marker).write_text('{}')
                with self.assertRaisesRegex(ValueError,'forbidden after selection'):
                    recovery.recover(run,Path(directory)/'missing-history')
                self.assertEqual({p.name for p in run.iterdir()},{marker})

    def test_changed_seed_in_source_rejects_cache_before_copying(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);run=root/'run';run.mkdir();old=root/'previous';old.mkdir()
            (old/'code').mkdir();(root/'research/smishguard').mkdir(parents=True)
            source=b'SEED = 20261005\n'
            (old/'code/ensemble_mbert.py').write_bytes(source)
            (root/'research/smishguard/ensemble_mbert.py').write_bytes(b'SEED = 20261006\r\n')
            cfg=dict(baseline_seed=20260929,mbert_seed=20261005,versions={},
                code_sha256={'code/ensemble_mbert.py':hashlib.sha256(source).hexdigest()})
            write_json(old/'configuration.json',cfg);write_json(old/'dataset.json',[]);write_json(old/'splits.json',{})
            with patch.object(recovery,'ROOT',root),patch.object(recovery.e,'context',return_value=(cfg,[],{})):
                with self.assertRaisesRegex(ValueError,'source content differs'):
                    recovery.recover(run,old)
            self.assertEqual(list(run.iterdir()),[])


if __name__=='__main__':
    unittest.main()
