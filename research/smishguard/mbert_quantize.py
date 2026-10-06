"""Separate INT8 deployment experiment; never fits, retunes or replaces frozen assets."""
import argparse
from collections import Counter
import platform
from pathlib import Path
import shutil
import time
import numpy as np
from scipy.special import expit
from .validation_stage import read, save, sha, now, ROOT
from .review_packets import private_output


def convert(source, output):
    import onnx
    import onnxruntime as ort
    from onnxruntime.quantization import quantize_dynamic, QuantType
    private_output(output)
    metadata=read(source/'model.json')
    if metadata['quantized'] or metadata['precision']!='float32':raise ValueError('Requires preserved float32 source')
    original={p.name:sha(p) for p in source.iterdir() if p.is_file()}
    if original['model.onnx']!=metadata['model_sha256'] or original['vocab.txt']!=metadata['vocab_sha256']:
        raise ValueError('Source integrity failed')
    output.mkdir(parents=True,exist_ok=False);assets=output/'app-assets';assets.mkdir()
    # Fixed before scoring: quantize constant MatMul weights and embedding Gather.
    # Dynamic activation quantization requires no calibration/test messages.
    config=dict(op_types_to_quantize=['MatMul','Gather'],per_channel=True,reduce_range=False,
                extra_options={'MatMulConstBOnly':True})
    quantize_dynamic(str(source/'model.onnx'),str(assets/'model.onnx'),weight_type=QuantType.QInt8,**config)
    onnx.checker.check_model(str(assets/'model.onnx'))
    for name in ('vocab.txt','LICENSE.txt'):shutil.copyfile(source/name,assets/name)
    metadata.update(model_version=metadata['model_version']+'-int8-v1',quantized=True,precision='int8_dynamic',
                    evaluation_status='experimental_quantization',reference_model_sha256=original['model.onnx'],
                    model_sha256=sha(assets/'model.onnx'))
    save(assets/'model.json',metadata)
    graph=onnx.load(str(assets/'model.onnx'))
    save(output/'conversion.json',dict(created_utc=now(),source_files=original,
        variant_files={p.name:sha(p) for p in assets.iterdir()},configuration=config,weight_type='QInt8',
        onnxruntime=ort.__version__,onnx=onnx.__version__,operators=dict(Counter(n.op_type for n in graph.graph.node)),
        float32_bytes=(source/'model.onnx').stat().st_size,int8_bytes=(assets/'model.onnx').stat().st_size,
        retrained=False,retuned=False,reporting_enabled=False))
    if any(sha(source/name)!=h for name,h in original.items()):raise ValueError('Original asset changed')
    print('Separate quantized asset prepared; original asset hashes verified.',flush=True)


def session(path):
    import onnxruntime as ort
    options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
    options.enable_cpu_mem_arena=False;options.enable_mem_pattern=False
    return ort.InferenceSession(str(path),options,providers=['CPUExecutionProvider'])


def benchmark(source, output, historical=None):
    private_output(output)
    from transformers import BertTokenizer
    from .mbert_experiment import redacted_case_view
    from .preliminary_compare import PROBES
    from .evaluate import metrics
    metadata=read(source/'model.json');variant=read(output/'app-assets/model.json');conversion=read(output/'conversion.json')
    for directory,files in ((source,conversion['source_files']),(output/'app-assets',conversion['variant_files'])):
        if any(sha(directory/name)!=h for name,h in files.items()):raise ValueError('Experiment assets changed')
    for key in ('threshold','calibration','vocab_sha256','max_length','tokenizer'):
        if metadata[key]!=variant[key]:raise ValueError('Frozen inference policy changed')
    tokenizer=BertTokenizer(vocab_file=str(source/'vocab.txt'),do_lower_case=False,strip_accents=False)
    def encode(text):
        return dict(tokenizer(redacted_case_view(text),max_length=metadata['max_length'],truncation=True,padding='max_length',return_tensors='np'))
    probes=list(PROBES)+['Hello HELLO hello','Kumusta po, bayad na ang utang.','你好，账户信息。','नमस्ते','é ñ İ 😀','[CLS] [MASK] [SEP]','hello '*300]
    texts=list(probes);labels=None
    if historical:
        rows=read(historical/'dataset.json');indices=read(historical/'splits.json')['partitions']['test']
        views={r['id']:r['text'] for r in read(historical/'case-view.json')}
        texts.extend(views[rows[i]['id']] for i in indices);labels=np.array([rows[i]['label'] for i in indices])
    inputs=[encode(t) for t in texts];logits={};timings={};load_ms={}
    # Sequential sessions avoid retaining two large runtimes in memory.
    for name,path in (('float32',source/'model.onnx'),('int8',output/'app-assets/model.onnx')):
        start=time.perf_counter();runtime=session(path);load_ms[name]=(time.perf_counter()-start)*1000
        logits[name]=np.array([runtime.run(None,feed)[0][0] for feed in inputs],dtype=np.float64)
        for i in range(20):runtime.run(None,inputs[i%len(probes)])
        durations=[]
        for i in range(100):
            start=time.perf_counter();runtime.run(None,inputs[i%len(probes)]);durations.append((time.perf_counter()-start)*1000)
        timings[name]=dict(warmups=20,scans=100,p50_ms=float(np.median(durations)),p95_ms=float(np.quantile(durations,.95)))
        del runtime
        print(name,'host inference complete',flush=True)
    cal=metadata['calibration'];threshold=metadata['threshold']
    scores={name:expit(cal['a']*(v[:,1]-v[:,0])+cal['b']) for name,v in logits.items()}
    changes=(scores['float32']>=threshold)!=(scores['int8']>=threshold)
    cases=[]
    for i,text in enumerate(probes):
        cases.append(dict(text=redacted_case_view(text),**{k:v[0].tolist() for k,v in inputs[i].items()},
                          logits=logits['int8'][i].tolist(),score=float(scores['int8'][i]),suspicious=bool(scores['int8'][i]>=threshold)))
    parity=output/'android-test-assets';parity.mkdir(exist_ok=False)
    save(parity/'mbert-private-cases.json',cases)
    result=dict(status='separate experimental INT8 deployment; never substitutes a frozen evaluation model',
        host=platform.platform(),threads=2,provider='CPUExecutionProvider',created_utc=now(),
        synthetic_cases=len(probes),historical_cases=0 if labels is None else len(labels),
        threshold=threshold,model_load_ms=load_ms,warm_inference=timings,
        max_logit_difference=float(np.abs(logits['float32']-logits['int8']).max()),
        max_score_difference=float(np.abs(scores['float32']-scores['int8']).max()),
        mean_score_difference=float(np.abs(scores['float32']-scores['int8']).mean()),
        synthetic_decision_changes=int(changes[:len(probes)].sum()),
        historical_decision_changes=int(changes[len(probes):].sum()),
        accuracy=None,physical_phone='pending actual evidence',
        limitation='Host timings are sequential engineering measurements, not physical-phone speed or a common-session four-model benchmark.')
    if labels is not None:
        result['accuracy']={name:metrics(labels,p[len(probes):],threshold) for name,p in scores.items()}
        result['accuracy_status']='Previously opened retrospective test with inherited unconfirmed labels; not fresh accuracy'
        result['historical_dataset_sha256']=sha(historical/'dataset.json')
        result['historical_split_sha256']=sha(historical/'splits.json')
    save(output/'benchmark.json',result)
    save(output/'private-predictions.json',dict(scores={k:v.tolist() for k,v in scores.items()},labels=None if labels is None else labels.tolist()))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['convert','benchmark'])
    p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--historical',type=Path)
    args=p.parse_args()
    if args.command=='convert':convert(args.source,args.output)
    else:benchmark(args.source,args.output,args.historical)
