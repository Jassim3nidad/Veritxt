# Manual light/dark theme restored — 20 October 2026

The UI packaged in the earlier APKs called `isSystemInDarkTheme()` directly and had no manual theme preference or Settings selector. That system-only behavior was already present in the checked-in UI and was missed during model packaging. Both palettes existed, but users could only change appearance through the phone's setting.

Settings → Preferences → **Theme** now offers **Follow system**, **Light mode**, and **Dark mode**. Changes apply immediately to the app colours, glass surfaces, risk colours and system-bar icon contrast. The selection is saved in the existing local DataStore and restored after activity recreation and a process restart. Missing/unknown stored values default to Follow system; clearing local preferences resets that choice. English and Filipino labels are included. Display preferences are already covered by the existing privacy notice.

Both current model variants were rebuilt. The frozen SVM model/adapter and retrained NB model hashes match their earlier delivered APK assets exactly. Fitted weights, preprocessing, thresholds and training/test partitions are preserved; the classifier comparison remains a comparison of the same models. Earlier APK files are retained at their original paths.

## Verification

- Both app/test APK builds passed, with lint reporting zero errors (11 existing warnings each).
- JVM: SVM 43 passed / 6 conditional skips; NB 39 passed / 10 conditional skips; zero failures or errors. Supplied private model parity checks ran for each variant.
- Eight API 36 emulator instrumentation invocations passed: on each APK, manual light/dark selection, Follow system, activity recreation and process restart were checked with the phone in both light and dark modes. The real bundled detector type was verified in each test.
- Tests checked the actual rendered light/dark background pixels and status/navigation-bar icon contrast, not just saved preference values. Native screenshots were inspected for both palettes. A further theme-control test at font scale 2.0 checks wrapping and scrolling.
- Both delivered APK signatures verify with the same local Android debug certificate. Asset inventories contain only the pinned model assets; no test fixtures are included. No physical phone was changed or tested.

## Delivery

Directory: `deliverables/Veritxt-Theme-Restored-20261020/`.

| APK | SHA-256 |
|---|---|
| `Veritxt-LinearSVM-60-20-20-Theme-Restored-20261020.apk` | `d0acbd3ecf350f9987aa3a8d02aa1ec0198158aabbe29f221a338e116d921136` |
| `Veritxt-Retrained-NB-80-20-Theme-Restored-20261020.apk` | `ee8b0b86551491f5d7c22381db3ae580b0d72ba253ffcf9ef52e36b76796087a` |

Application IDs and signing identities match the earlier respective builds, so each APK can update its corresponding installed app. Android 8.0+ is supported. Verification JSON, screenshots, build metadata and `SHA256SUMS.txt` accompany the delivery. Detailed local logs remain in `research/runs/theme-restoration-20261020/`.
