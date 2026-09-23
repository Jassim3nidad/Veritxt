# SMISHGUARD reporting backend

A local development prototype prepared for possible future reporting integration after approval and security controls are completed.

Flask accepts local synthetic contract fixtures and shows aggregate views; Android is not connected. It accepts **exactly** the payload defined by
`ReportPayload.json()` in `android/app/src/main/java/ph/smishguard/privacy/Reports.kt`
and rejects everything else.

No dataset, model file or real report is included.

## Run

```
pip install -r requirements.txt
python seed.py        # optional: 120 invented demo rows
python app.py         # http://127.0.0.1:5000
```

Test:

```
python -m unittest test_backend -v
```

The supplied baseline had 37 tests; this integration has 45 tests. They use a temporary database and never touch `smishguard_reports.db`.

## Status

The app does not send reports yet. Its APK has no INTERNET permission and its
`ReportingRepository` is `DisabledReportingRepository`. This server is the
receiving-side prototype, with deployment and connection still unapproved. It does
not change that decision.

## Endpoint

`POST /api/reports` with one JSON object per request:

```json
{
  "domain": "gcash-verify.ph",
  "score": 0.9576,
  "predicted_class": "suspicious",
  "date_hour": "2026-09-23T21+08:00",
  "city": "Dasmariñas",
  "brand": "GCash"
}
```

Returns `201 {"stored": true}` or `400 {"error": "..."}` explaining what was
wrong.

| Field | Rule | Mirrors |
|---|---|---|
| `domain` | `null`, or one registered label on an allowed suffix: lowercase letters and hyphens, no digits, no subdomains, no `xn--`, no scheme or path | `SafeDomain.fromUrl` |
| `score` | finite number, 0 to 1 | `Detection.Success.score` |
| `predicted_class` | `suspicious` or `not_suspicious` | `ReportPayload.create` |
| `date_hour` | hour only with offset, e.g. `2026-09-23T21+08:00` or `2026-09-23T13Z`. Minutes are rejected. | `yyyy-MM-dd'T'HHXXX` |
| `city` | `Dasmariñas`, `Bacoor`, `Imus`, `Manila`, `Other city` | `City` enum, minus "Not selected" |
| `brand` | optional: `BDO`, `BPI`, `GCash`, `Maya`, `SSS`, `Other financial institution` | `Brand` enum; omitted when unspecified |

Allowed suffixes: `com org net edu gov io ph com.ph org.ph net.ph gov.ph edu.ph co.uk`.

Any other key is rejected, including `message`, `sender`, `source`,
`flagged_at_ms` and `is_demo`. Bodies over 4 KB are rejected.

`date_hour` accepts UTC (`Z`), Manila and half/quarter-hour offsets. The backend limits offsets to +/-14:00 (narrower than Java's theoretical +/-18:00 range), rejects invalid offset minutes and UTC-conversion overflow, and rejects timestamps more than 14 hours ahead. This is an explicit server restriction beyond Android formatting.

## Privacy

- The database has no column for message text, phone number, sender, device
  ID or IP address, and validation rejects additional keys. This does not replace infrastructure privacy review.
- The development server's access log is silenced, because it prints client
  IP addresses (`docs/privacy.md`: do not store IP/access logs as research
  metadata).
- Times arrive already rounded to the hour by the app. Minute-level times are
  refused rather than rounded, so a mismatched client fails loudly.
- Optional shared secret: set `SMISHGUARD_TOKEN` and the endpoint requires
  `Authorization: Bearer <token>`.

## Dashboard

Shows report count, suspicious count, last 24 hours and 7 days, null-domain
count, and breakdowns by city, brand and domain.

- Scores are shown as `0.87`, never `87%`. The contract calls them uncalibrated
  model scores, not probabilities.
- `/` excludes demo rows from every aggregate and recent list; `/?demo=1` shows only invented rows. Demo rows are marked `demo` on each row, and a banner states how many rows
  are invented. Every demo domain contains `demo`.
- The footer states that counts are voluntary reports, not citywide scam
  prevalence or distinct victims, and that a null domain means none was sent,
  not that the message had no link.

## Not done yet

Taken from `backend/README.md` in the app repo. All of these are needed before
this runs anywhere except a laptop on a closed network:

- TLS (the development server is plain HTTP)
- staff login and access roles for the dashboard
- rate limits that do not collect device identifiers
- retention and deletion policy
- abuse handling
- partner acceptance and a security review
- a production WSGI server instead of `python app.py`

## Local-only safeguards and dependencies

Bind only to 127.0.0.1 (the default of `python app.py`); do not deploy publicly. The optional POST bearer secret is not staff authentication or role authorization, and the dashboard has no authentication. All deployment gates remain pending in [reporting readiness](../docs/reporting-readiness.md). No app endpoint or INTERNET permission was added.

Create an isolated environment (`python -m venv .venv`) and install requirements there. Requirements now pin the resolved runtime and transitive packages; the original Flask>=3.0,<4 range was not reproducible. Pins are not a security guarantee or a hash-locked supply chain. No external fonts or browser resource requests remain in the template. The server does not intentionally log request bodies; Werkzeug access logging is suppressed. Production proxy/error/access logging requires separate review. Database creation occurs on module import; tests redirect it to temporary storage. Only invented fixtures were submitted during this integration.
