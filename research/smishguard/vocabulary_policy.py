"""Identifier screening adapted from Mark's export builder; never edit fitted weights.

A clean pattern screen is not human redaction approval or proof of no personal data.
Deterministic selection is available for future reviewed training, not enabled in
the frozen comparison protocol by this module.
"""
import re

DIGITS = re.compile(r"\d{5,}")
MASKED = re.compile(r"x{3,}\d|\d+x{3,}|\*{2,}", re.I)


def identifier_like(term):
    return any(DIGITS.search(part) or MASKED.search(part) for part in term.split())


def select_terms(terms, totals, limit):
    if len(terms) != len(totals) or len(set(terms)) != len(terms) or limit < 1:
        raise ValueError("Invalid vocabulary selection input")
    candidates = [(int(count), term) for term, count in zip(terms, totals) if not identifier_like(term)]
    return [term for _, term in sorted(candidates, key=lambda pair: (-pair[0], pair[1]))[:limit]]


def screen(vocabulary):
    terms = list(vocabulary)
    return dict(features=len(terms), identifier_pattern_features=sum(identifier_like(t) for t in terms),
                long_digit_features=sum(bool(DIGITS.search(t)) for t in terms),
                masked_identifier_features=sum(bool(MASKED.search(t)) for t in terms),
                scope="automated patterns only; no human privacy/research acceptance inferred")
