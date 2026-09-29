"""
SMISHGUARD voluntary reporting backend.

Accepts exactly the payload the Android app's ReportPayload.json() produces
(ph.smishguard.privacy.Reports.kt in Jassim3nidad/SMISHGUARD) and nothing else.

    python app.py            ->  http://127.0.0.1:5000

The app does not call this yet. Its APK has no INTERNET permission and its
ReportingRepository is a disabled implementation. This server is the receiving
side of a local readiness prototype, pending approval and security controls.
"""

import hmac
import logging
import math
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, g, jsonify, render_template, request

BASE_DIR = Path(__file__).parent
DB_PATH = Path(os.environ.get("SMISHGUARD_DB", BASE_DIR / "smishguard_reports.db"))

# --- The contract. Every value below mirrors Reports.kt exactly. ---------------

REQUIRED_FIELDS = {"domain", "score", "predicted_class", "date_hour", "city"}
OPTIONAL_FIELDS = {"brand"}

PREDICTED_CLASSES = {"suspicious", "not_suspicious"}

# City.label values, minus NOT_SELECTED: ReportPayload.create() refuses to build
# a payload without a selected city, so "Not selected" never arrives legitimately.
CITIES = {"Dasmariñas", "Bacoor", "Imus", "Manila", "Other city"}

# Brand.label values, minus UNSPECIFIED: the app omits the key entirely instead.
BRANDS = {"BDO", "BPI", "GCash", "Maya", "SSS", "Other financial institution"}

# SafeDomain: one registered label directly above a known suffix, no subdomains.
DOMAIN_SUFFIXES = {"com", "org", "net", "edu", "gov", "io", "ph",
                   "com.ph", "org.ph", "net.ph", "gov.ph", "edu.ph", "co.uk"}
DOMAIN_ROOT = re.compile(r"[a-z][a-z-]{0,38}[a-z]|[a-z]")

# DateTimeFormatter "yyyy-MM-dd'T'HHXXX": hour only, with offset. XXX writes "Z"
# for UTC and "+08:00" otherwise.
DATE_HOUR = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2})(Z|[+-][0-9]{2}:[0-9]{2})")

MAX_BODY_BYTES = 4096
FUTURE_TOLERANCE = timedelta(hours=14)   # widest real UTC offset

# Optional shared secret: when set, POST needs "Authorization: Bearer <token>".
AUTH_TOKEN = os.environ.get("SMISHGUARD_TOKEN")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_BODY_BYTES
app.json.ensure_ascii = False   # keep city names readable in responses

# The contract: "Do not store IP/access logs as research/report metadata."
# Werkzeug's development server prints the client IP for every request, so
# silence its access log. Errors are still shown.
logging.getLogger("werkzeug").setLevel(logging.ERROR)


@app.after_request
def security_headers(response):
    """Compatible handoff hardening; local resources only, including error pages."""
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


# --- Storage -------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    # No column for message text, phone number, sender, device ID or IP address,
    # so none of those can be stored even by mistake. is_demo is server-side
    # only - it is never accepted from a client.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            domain          TEXT,
            score           REAL    NOT NULL,
            predicted_class TEXT    NOT NULL,
            date_hour       TEXT    NOT NULL,
            hour_utc        TEXT    NOT NULL,
            city            TEXT    NOT NULL,
            brand           TEXT,
            is_demo         INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


# --- Validation ----------------------------------------------------------------

def valid_domain(value):
    """True if value is something SafeDomain.fromUrl could have produced."""
    if not isinstance(value, str) or value != value.lower():
        return False
    for suffix in sorted(DOMAIN_SUFFIXES, key=len, reverse=True):
        if value.endswith("." + suffix):
            root = value[: -(len(suffix) + 1)]
            return ("." not in root and not root.startswith("xn--")
                    and DOMAIN_ROOT.fullmatch(root) is not None)
    return False


def parse_date_hour(value):
    """Returns the hour as a UTC datetime, or None if it is not hour-only ISO."""
    if not isinstance(value, str):
        return None
    m = DATE_HOUR.fullmatch(value)
    if not m:
        return None
    year, month, day, hour, offset = m.groups()
    try:
        if offset == "Z":
            tz = timezone.utc
        else:
            sign = 1 if offset[0] == "+" else -1
            oh, om = int(offset[1:3]), int(offset[4:6])
            if oh > 14 or om > 59 or (oh == 14 and om != 0):
                return None
            tz = timezone(sign * timedelta(hours=oh, minutes=om))
        local = datetime(int(year), int(month), int(day), int(hour), tzinfo=tz)
        return local.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def validate(payload):
    """Returns (record, error). Exactly one of them is None."""
    if not isinstance(payload, dict):
        return None, "body must be a single JSON object"

    unknown = set(payload) - REQUIRED_FIELDS - OPTIONAL_FIELDS
    if unknown:
        return None, "unknown fields rejected"
    missing = REQUIRED_FIELDS - set(payload)
    if missing:
        return None, "missing required fields: " + ", ".join(sorted(missing))

    domain = payload["domain"]
    if domain is not None and not valid_domain(domain):
        return None, ("domain must be null or a single registered domain on an "
                      "allowed suffix, e.g. example.com.ph - no subdomains, "
                      "digits, paths or schemes")

    score = payload["score"]
    if isinstance(score, bool) or not isinstance(score, (int, float)) \
            or not 0.0 <= score <= 1.0 or not math.isfinite(score):
        return None, "score must be a finite number between 0 and 1"

    if not isinstance(payload["predicted_class"], str) or payload["predicted_class"] not in PREDICTED_CLASSES:
        return None, "predicted_class must be 'suspicious' or 'not_suspicious'"

    hour_utc = parse_date_hour(payload["date_hour"])
    if hour_utc is None:
        return None, ("date_hour must be hour-only ISO 8601 with an offset, "
                      "e.g. 2026-09-23T21+08:00 - minutes are not accepted")
    if hour_utc > datetime.now(timezone.utc) + FUTURE_TOLERANCE:
        return None, "date_hour is in the future"

    if not isinstance(payload["city"], str) or payload["city"] not in CITIES:
        return None, "city must be one of: " + ", ".join(sorted(CITIES))

    brand = payload.get("brand")
    if "brand" in payload and (not isinstance(brand, str) or brand not in BRANDS):
        return None, "brand must be omitted or one of: " + ", ".join(sorted(BRANDS))

    return {
        "domain": domain,
        "score": float(score),
        "predicted_class": payload["predicted_class"],
        "date_hour": payload["date_hour"],
        "hour_utc": hour_utc.isoformat(),
        "city": payload["city"],
        "brand": brand,
    }, None


def check_auth():
    if not AUTH_TOKEN:
        return None
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer ") or \
            not hmac.compare_digest(header[len("Bearer "):].encode("utf-8"), AUTH_TOKEN.encode("utf-8")):
        return jsonify(error="unauthorized"), 401
    return None


# --- Routes --------------------------------------------------------------------

@app.post("/api/reports")
def ingest():
    """One report per request: the exact body of ReportPayload.json()."""
    unauthorised = check_auth()
    if unauthorised:
        return unauthorised
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify(error="body must be JSON"), 400
    record, error = validate(payload)
    if error:
        return jsonify(error=error), 400
    db = get_db()
    db.execute(
        "INSERT INTO reports (domain, score, predicted_class, date_hour, hour_utc, city, brand) "
        "VALUES (:domain, :score, :predicted_class, :date_hour, :hour_utc, :city, :brand)",
        record,
    )
    db.commit()
    return jsonify(stored=True), 201


@app.errorhandler(413)
def too_large(_):
    return jsonify(error=f"body larger than {MAX_BODY_BYTES} bytes"), 413


@app.get("/api/health")
def health():
    return jsonify(status="ok", requires_token=bool(AUTH_TOKEN))


def tally(rows, key, missing_label):
    counts = {}
    for r in rows:
        name = r[key] or missing_label
        counts[name] = counts.get(name, 0) + 1
    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)


@app.get("/")
def dashboard():
    # One cohort per page: invented rows never enter voluntary-report totals.
    demo = request.args.get("demo") == "1"
    rows = get_db().execute(
        "SELECT * FROM reports WHERE is_demo = ? ORDER BY hour_utc DESC, id DESC",
        (int(demo),)).fetchall()
    now = datetime.now(timezone.utc)
    day_ago = (now - timedelta(hours=24)).isoformat()
    week_ago = (now - timedelta(days=7)).isoformat()

    suspicious = [r for r in rows if r["predicted_class"] == "suspicious"]
    return render_template(
        "dashboard.html",
        demo_view=demo,
        total=len(rows),
        demo_count=sum(r["is_demo"] for r in rows),
        suspicious=len(suspicious),
        last_24h=sum(1 for r in rows if r["hour_utc"] >= day_ago),
        last_7d=sum(1 for r in rows if r["hour_utc"] >= week_ago),
        no_domain=sum(1 for r in rows if r["domain"] is None),
        by_city=tally(rows, "city", "-"),
        by_brand=tally(suspicious, "brand", "Not specified"),
        top_domains=tally([r for r in suspicious if r["domain"]], "domain", "")[:10],
        recent=[{
            "domain": r["domain"],
            "brand": r["brand"] or "Not specified",
            "city": r["city"],
            "date_hour": r["date_hour"],
            "score": f"{r['score']:.2f}",
            "suspicious": r["predicted_class"] == "suspicious",
            "demo": bool(r["is_demo"]),
        } for r in rows[:25]],
    )


# Runs at import so the table exists however the server is started.
init_db()

if __name__ == "__main__":
    app.run(port=5000)
