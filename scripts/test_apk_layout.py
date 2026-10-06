import io
from pathlib import Path
import tempfile
import unittest
import zipfile
from audit_apk_layout import audit


class ApkLayout(unittest.TestCase):
    def test_finds_unreferenced_prefix_without_changing_entries(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('assets/fictional.txt','fictional test payload')
        with tempfile.TemporaryDirectory() as tmp:
            original=Path(tmp)/'original.apk';bloated=Path(tmp)/'bloated.apk'
            original.write_bytes(b.getvalue());bloated.write_bytes(b'x'*2097152+b.getvalue())
            a,c=audit(original),audit(bloated)
            self.assertEqual(a['gap_bytes'],0)
            self.assertEqual(c['gap_bytes'],2097152)
            self.assertEqual(a['referenced_stored_bytes'],c['referenced_stored_bytes'])


if __name__=='__main__':unittest.main()
