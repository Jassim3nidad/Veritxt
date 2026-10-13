"""Safe probes against unchanged supplied active parameters; never exports SMS."""
from pathlib import Path
import argparse
import json
import re
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from smishguard.convert_supplied import portable,validate
from smishguard.bantaytext_workflow import save


def main():
    p=argparse.ArgumentParser();p.add_argument('parity',type=Path);a=p.parse_args()
    model=validate(json.loads((ROOT/'research/data/package-audit/original/model_export_final.json').read_text(encoding='utf-8-sig')))
    probes=['Hello po, kumusta ang inyong araw?', 'Your OTP is 123456. Do not share it.',
        'BDO statement available sa app', 'GCash transaction completed. Check your official app.',
        'Pakisuri ang account sa opisyal na app.', 'paki verify nyo ninyo na po',
        'Verify account at https://example.invalid/synthetic', '', '   ', 'qzxvunknownword zzzqqq',
        'asdfghjkl', '123456', 'https://example.invalid/synthetic', '🙂 ñ café İ', '\ud800', 'x'*10001]
    cases=[dict(text=t,tokens=re.findall(r'\b\w+\b',t.lower()),score=portable(model,t),suspicious=portable(model,t)>.5,
                must_abstain=t in ('','   ','qzxvunknownword zzzqqq','asdfghjkl','123456','https://example.invalid/synthetic','\ud800')) for t in probes]
    # ASCII-escape lone surrogates: deliberately malformed input is still valid JSON.
    (a.parity/'active-cases.json').write_text(json.dumps(cases,ensure_ascii=True,allow_nan=False),encoding='utf-8')
    shutil.copy2(ROOT/'android/app/src/development/assets/model.json',a.parity/'active-model.json')
    print('Active-model safe probes prepared privately:',len(cases))


if __name__=='__main__':main()
