"""Measure referenced ZIP entries and unreferenced gaps without extracting weights."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile


def audit(path):
    with path.open('rb') as stream, zipfile.ZipFile(path) as archive:
        entries=[]; end=0; gaps=[]
        for item in sorted(archive.infolist(),key=lambda i:i.header_offset):
            if item.header_offset>end:gaps.append({'offset':end,'bytes':item.header_offset-end})
            stream.seek(item.header_offset)
            header=stream.read(30)
            assert header[:4]==b'PK\x03\x04'
            name,extra=struct.unpack_from('<HH',header,26)
            start=item.header_offset+30+name+extra
            end=start+item.compress_size
            if item.flag_bits&8:
                stream.seek(end); descriptor=stream.read(4)
                end+=16 if descriptor==b'PK\x07\x08' else 12
            entries.append(dict(name=item.filename,bytes=item.file_size,stored_bytes=item.compress_size,
                                offset=item.header_offset,data_offset=start,end=end))
        if archive.start_dir>end:gaps.append({'offset':end,'bytes':archive.start_dir-end})
        # Gap hashes identify redundant bytes; neither bytes nor strings are printed.
        for gap in gaps:
            stream.seek(gap['offset']);remaining=gap['bytes'];h=hashlib.sha256()
            while remaining:
                block=stream.read(min(remaining,1024*1024));h.update(block);remaining-=len(block)
            gap['sha256']=h.hexdigest()
        stream.seek(0);digest=hashlib.file_digest(stream,'sha256').hexdigest()
    return dict(apk_sha256=digest,apk_bytes=path.stat().st_size,entries=entries,
                referenced_stored_bytes=sum(i['stored_bytes'] for i in entries),
                gaps=gaps,gap_bytes=sum(g['bytes'] for g in gaps),
                note='Gaps are outside referenced local entry records; include alignment/signing blocks and possibly obsolete incremental payloads.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('apk',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    result=audit(a.apk)
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:result[k] for k in ('apk_bytes','referenced_stored_bytes','gap_bytes')}))
