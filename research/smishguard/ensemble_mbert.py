"""Fixed-setting mBERT fits for the separate ensemble experiment (local only)."""
import gc
import math
from pathlib import Path
import random
import time

import numpy as np
from sklearn.metrics import average_precision_score

from . import fair_compare as fair
from .mbert_experiment import imports
from .train import write_json

SEED = 20261005


def fit(base, rows, train_ids, output, validation_ids=None):
    """Baseline selects on validation; stacking uses exactly two fixed epochs."""
    torch, Model, Tokenizer, Adafactor = imports()
    if not torch.cuda.is_available():
        raise RuntimeError('Configured CUDA training unavailable')
    output.mkdir(parents=True, exist_ok=False)
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(4)
    torch.cuda.reset_peak_memory_stats()
    tokenizer = Tokenizer.from_pretrained(base, local_files_only=True, do_lower_case=False)
    lengths = [len(tokenizer(rows[i]['text'], truncation=False)['input_ids']) for i in train_ids]
    length = min(256, max(64, int(math.ceil(float(np.percentile(lengths, 95))/16)*16)))
    model = Model.from_pretrained(
        base, num_labels=2, id2label={0:'ham', 1:'smishing'}, label2id={'ham':0, 'smishing':1},
        local_files_only=True, use_safetensors=True, attn_implementation='eager').cuda()
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    optimizer = Adafactor(model.parameters(), lr=2e-5, relative_step=False,
                         scale_parameter=False, warmup_init=False, weight_decay=.01)
    scaler = torch.amp.GradScaler('cuda')

    def encode(indices):
        return {k:v.cuda() for k,v in tokenizer([rows[i]['text'] for i in indices],
            max_length=length, truncation=True, padding='max_length', return_tensors='pt').items()}

    started = time.perf_counter()
    history, best, selected = [], -1., None
    write_json(output/'configuration.json', dict(seed=SEED, epochs=2, learning_rate=2e-5,
        weight_decay=.01, optimizer='Adafactor', microbatch=1, gradient_accumulation=8,
        max_length=length, wall_budget_seconds=2700, train_indices=list(map(int,train_ids)),
        checkpoint_validation_indices=None if validation_ids is None else list(map(int,validation_ids)),
        checkpoint_policy='fixed_epoch_2' if validation_ids is None else 'validation_average_precision'))
    for epoch in range(2):
        order = np.random.default_rng(SEED+epoch).permutation(train_ids).tolist()
        model.train()
        losses = []
        for start in range(0, len(order), 8):
            if time.perf_counter()-started > 2700:
                raise RuntimeError('Preserved 2700-second mBERT fit budget exceeded')
            chunk = order[start:start+8]
            optimizer.zero_grad(set_to_none=True)
            for i in chunk:
                with torch.autocast('cuda', dtype=torch.float16):
                    loss = model(**encode([i]), labels=torch.tensor([rows[i]['label']],device='cuda')).loss/len(chunk)
                scaler.scale(loss).backward()
                losses.append(float(loss.detach())*len(chunk))
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
            scaler.step(optimizer)
            scaler.update()
            if (start+8)%200 == 0:
                print(output.name, 'epoch', epoch+1, 'records', start+8, '/', len(order), flush=True)
        ap = None
        if validation_ids is not None:
            model.eval()
            with torch.no_grad():
                logits = np.array([model(**encode([i])).logits.float().cpu().numpy()[0] for i in validation_ids])
            ap = float(average_precision_score([rows[i]['label'] for i in validation_ids], logits[:,1]-logits[:,0]))
            if ap > best:
                best, selected = ap, epoch+1
                model.save_pretrained(output/'selected', safe_serialization=True)
                tokenizer.save_pretrained(output/'selected')
        history.append(dict(epoch=epoch+1, validation_average_precision=ap, mean_loss=float(np.mean(losses))))
        print(output.name, 'completed epoch', epoch+1, 'validation AP', ap, flush=True)
    # Fixed-epoch stacking weights must not depend on outer validation selection.
    if validation_ids is None or selected != 2:
        model.save_pretrained(output/'final', safe_serialization=True)
        tokenizer.save_pretrained(output/'final')
    summary = dict(seconds=time.perf_counter()-started, history=history, max_length=length,
        selected_epoch=selected, fixed_epoch=2, train_records=len(train_ids),
        train_truncated=sum(n>length for n in lengths), gpu=torch.cuda.get_device_name(),
        peak_cuda_bytes=torch.cuda.max_memory_allocated(), complete=True,
        selected_path='selected' if validation_ids is not None else 'final',
        final_path='selected' if selected == 2 else 'final')
    write_json(output/'training-summary.json', summary)
    del model, optimizer, scaler
    gc.collect()
    torch.cuda.empty_cache()
    return summary


def logits(checkpoint, texts, length, device='cpu'):
    """Timing includes tokenization, excludes loading. Defaults to common CPU inference."""
    torch, Model, Tokenizer, _ = imports()
    torch.set_num_threads(4)
    model = Model.from_pretrained(checkpoint, local_files_only=True, attn_implementation='eager').to(device).eval()
    tokenizer = Tokenizer.from_pretrained(checkpoint, local_files_only=True)
    started = time.perf_counter()
    values = []
    with torch.no_grad():
        for text in texts:
            encoded = {k:v.to(device) for k,v in tokenizer([text],max_length=length,
                truncation=True,padding='max_length',return_tensors='pt').items()}
            values.append(model(**encoded).logits.float().cpu().numpy()[0])
    elapsed = time.perf_counter()-started
    del model
    gc.collect()
    if device == 'cuda':
        torch.cuda.empty_cache()
    return np.array(values), elapsed
