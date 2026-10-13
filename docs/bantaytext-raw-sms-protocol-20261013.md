# Raw SMS preprocessing validation

This check closes the selected SVM's raw-input engineering gap without changing its
fitted vocabulary, coefficients, IDF, calibration, threshold or original evaluations.

Reproduce the actual training view: `clean(mask(clean(raw SMS)))`. `clean` removes
the documented dataset placeholder spans, collapses Python Unicode whitespace and
strips edge spaces/commas. `mask` substitutes ASCII-case-insensitive http(s)/www URLs,
ASCII email addresses and ASCII digit runs with zzurlzz/zzemailzz/zznumberzz, in that
order. Then apply the existing frozen Unicode word>=2/English-stopword/bigram scorer.
Bare domains and obfuscated URLs retain the original preparation behavior; this is
compatibility, not a new URL detector or a privacy certification.

Validate all 2,554 cleaned records against their pinned original-source join on the
host without exporting raw message text. Verify Python and test-only Kotlin masking,
tokens, feature indices/values, scores, threshold decisions and abstention on a frozen
synthetic raw-SMS probe set. Real raw messages remain in authorized private source
storage; Android probes contain only fictional inputs. No network request is made.

The candidate remains test-only until a defensible release decision. The original
task permits inherited labels when human review is unavailable, with explicit
limitations; independent human labeling is not an additional blanket software gate.
Historically exposed tests cannot establish prospective traffic performance, and
the observed source-transfer weakness remains a substantive model-selection issue.

Physical-phone checks are completed as directly reported by the user on 13 October
2026. The exact tested APK/model and measurement details were not specified in this
chat; record the report without inventing device timings or attributing those checks
to the newly exported SVM. Previous agent-run checks remain explicitly emulator-only.
