"""App-policy correction: preprocessing placeholders are not meaningful message words.

Separate from frozen classifier/research results. Never changes learned parameters.
"""
from .preliminary_compare import assessable as original_assessable

PLACEHOLDERS={'zznumberzz','zzemailzz','zzurlzz','zznamezz','zzaccountzz'}

def assessable(text,vocabulary):
    return original_assessable(text,set(vocabulary)-PLACEHOLDERS)
