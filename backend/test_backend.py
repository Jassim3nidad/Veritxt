"""
Checks the backend against the app's payload contract.

    python -m unittest test_backend -v

Uses a temporary database; your real smishguard_reports.db is not touched.
"""

import json
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

_tmp = tempfile.TemporaryDirectory()
os.environ["SMISHGUARD_DB"] = os.path.join(_tmp.name, "test.db")
os.environ.pop("SMISHGUARD_TOKEN", None)

import app as backend  # noqa: E402  (must import after the env vars are set)

PHT = timezone(timedelta(hours=8))
NOW_HOUR = datetime.now(PHT).replace(minute=0, second=0, microsecond=0)


def app_payload(**overrides):
    """The shape ReportPayload.json() produces on the phone."""
    body = {
        "domain": "gcash-verify.ph",
        "score": 0.9576,
        "predicted_class": "suspicious",
        "date_hour": NOW_HOUR.strftime("%Y-%m-%dT%H") + "+08:00",
        "city": "Dasmariñas",
        "brand": "GCash",
    }
    body.update(overrides)
    return {k: v for k, v in body.items() if v is not _DROP}


_DROP = object()


class ContractTest(unittest.TestCase):

    def test_security_headers_cover_pages_and_errors_without_external_resources(self):
        client = backend.app.test_client()
        for url in ('/', '/api/health', '/missing'):
            response = client.get(url)
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
            self.assertEqual(response.headers['Referrer-Policy'], 'no-referrer')
            self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
            self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
            self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy'])
            self.assertNotIn('https:', response.headers['Content-Security-Policy'])

    def setUp(self):
        backend.AUTH_TOKEN = None
        self.client = backend.app.test_client()
        conn = sqlite3.connect(backend.DB_PATH)
        conn.execute("DELETE FROM reports")
        conn.commit()
        conn.close()

    def post(self, body, **kw):
        return self.client.post("/api/reports", data=json.dumps(body),
                                content_type="application/json", **kw)

    def assert_rejected(self, body, fragment):
        r = self.post(body)
        self.assertEqual(r.status_code, 400, r.get_json())
        self.assertIn(fragment, r.get_json()["error"])

    # --- accepted ---------------------------------------------------------------

    def test_accepts_the_apps_payload(self):
        r = self.post(app_payload())
        self.assertEqual(r.status_code, 201, r.get_json())

    def test_accepts_null_domain_and_no_brand(self):
        r = self.post(app_payload(domain=None, brand=_DROP))
        self.assertEqual(r.status_code, 201, r.get_json())

    def test_accepts_utc_z_offset(self):
        hour = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H") + "Z"
        self.assertEqual(self.post(app_payload(date_hour=hour)).status_code, 201)

    def test_accepts_every_city_and_brand(self):
        for city in backend.CITIES:
            self.assertEqual(self.post(app_payload(city=city)).status_code, 201, city)
        for brand in backend.BRANDS:
            self.assertEqual(self.post(app_payload(brand=brand)).status_code, 201, brand)

    def test_accepts_every_allowed_suffix(self):
        for suffix in backend.DOMAIN_SUFFIXES:
            r = self.post(app_payload(domain=f"example.{suffix}"))
            self.assertEqual(r.status_code, 201, suffix)

    def test_accepts_not_suspicious(self):
        r = self.post(app_payload(predicted_class="not_suspicious", score=0.12))
        self.assertEqual(r.status_code, 201)

    # --- privacy: unknown and identifying fields ---------------------------------

    def test_rejects_message_text(self):
        self.assert_rejected(app_payload(message="Your GCash is locked"), "unknown fields")

    def test_rejects_phone_number_field(self):
        # Placeholder, not a real number: the key alone must be refused.
        self.assert_rejected(app_payload(sender="09XX-XXX-XXXX"), "unknown fields")

    def test_rejects_old_backend_fields(self):
        self.assert_rejected(app_payload(source="device"), "unknown fields")
        self.assert_rejected(app_payload(flagged_at_ms=1790000000000), "unknown fields")
        self.assert_rejected(app_payload(claimed_institution="GCash"), "unknown fields")

    def test_rejects_minutes_in_date_hour(self):
        hm = NOW_HOUR.strftime("%Y-%m-%dT%H") + ":15+08:00"
        self.assert_rejected(app_payload(date_hour=hm), "hour-only")

    def test_rejects_date_hour_without_offset(self):
        self.assert_rejected(app_payload(date_hour=NOW_HOUR.strftime("%Y-%m-%dT%H")), "hour-only")

    def test_rejects_epoch_millis(self):
        self.assert_rejected(app_payload(date_hour=1790000000000), "hour-only")

    def test_rejects_future_hour(self):
        later = (NOW_HOUR + timedelta(days=3)).strftime("%Y-%m-%dT%H") + "+08:00"
        self.assert_rejected(app_payload(date_hour=later), "future")

    def test_rejects_impossible_date(self):
        self.assert_rejected(app_payload(date_hour="2026-02-30T10+08:00"), "hour-only")

    # --- domain policy -------------------------------------------------------------

    def test_rejects_subdomain(self):
        self.assert_rejected(app_payload(domain="login.gcash-verify.ph"), "domain")

    def test_rejects_digits_in_domain(self):
        self.assert_rejected(app_payload(domain="gcash123.com"), "domain")

    def test_rejects_path_or_scheme(self):
        self.assert_rejected(app_payload(domain="https://gcash-verify.ph"), "domain")
        self.assert_rejected(app_payload(domain="gcash-verify.ph/login"), "domain")

    def test_rejects_unknown_suffix(self):
        self.assert_rejected(app_payload(domain="gcash-verify.xyz"), "domain")

    def test_rejects_uppercase_domain(self):
        self.assert_rejected(app_payload(domain="GCash-Verify.ph"), "domain")

    def test_rejects_punycode(self):
        self.assert_rejected(app_payload(domain="xn--gcsh-verify.ph"), "domain")

    # --- controlled choices ------------------------------------------------------

    def test_rejects_unselected_city(self):
        self.assert_rejected(app_payload(city="Not selected"), "city")

    def test_rejects_free_text_city(self):
        self.assert_rejected(app_payload(city="Brgy. Salitran, Dasmarinas"), "city")

    def test_rejects_unspecified_brand_label(self):
        self.assert_rejected(app_payload(brand="Not specified"), "brand")

    def test_rejects_free_text_brand(self):
        self.assert_rejected(app_payload(brand="Juan's bank"), "brand")

    def test_rejects_missing_city(self):
        self.assert_rejected(app_payload(city=_DROP), "missing")

    # --- score and class -----------------------------------------------------------

    def test_rejects_out_of_range_score(self):
        self.assert_rejected(app_payload(score=1.5), "score")
        self.assert_rejected(app_payload(score=-0.1), "score")

    def test_rejects_non_finite_score(self):
        r = self.client.post("/api/reports", content_type="application/json",
                             data=json.dumps(app_payload()).replace("0.9576", "NaN"))
        self.assertEqual(r.status_code, 400)

    def test_rejects_boolean_score(self):
        self.assert_rejected(app_payload(score=True), "score")

    def test_rejects_other_class_names(self):
        self.assert_rejected(app_payload(predicted_class="smishing"), "predicted_class")

    # --- request shape -----------------------------------------------------------

    def test_rejects_batch_array(self):
        self.assert_rejected([app_payload()], "single JSON object")

    def test_rejects_non_json(self):
        r = self.client.post("/api/reports", data="hello", content_type="text/plain")
        self.assertEqual(r.status_code, 400)

    def test_rejects_oversized_body(self):
        r = self.client.post("/api/reports", content_type="application/json",
                             data="{" + " " * 5000 + "}")
        self.assertEqual(r.status_code, 413)

    def test_token_required_when_set(self):
        backend.AUTH_TOKEN = "secret"
        self.assertEqual(self.post(app_payload()).status_code, 401)
        ok = self.post(app_payload(), headers={"Authorization": "Bearer secret"})
        self.assertEqual(ok.status_code, 201)

    # --- storage -----------------------------------------------------------------

    def test_stores_only_contract_fields(self):
        self.post(app_payload())
        conn = sqlite3.connect(backend.DB_PATH)
        conn.row_factory = sqlite3.Row
        row = dict(conn.execute("SELECT * FROM reports").fetchone())
        conn.close()
        self.assertEqual(set(row), {"id", "domain", "score", "predicted_class",
                                    "date_hour", "hour_utc", "city", "brand", "is_demo"})
        self.assertEqual(row["is_demo"], 0)
        self.assertTrue(row["hour_utc"].endswith(":00:00+00:00"))

    def test_client_cannot_mark_itself_demo(self):
        self.assert_rejected(app_payload(is_demo=1), "unknown fields")

    def test_dashboard_renders_with_and_without_data(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.post(app_payload())
        self.post(app_payload(domain=None, brand=_DROP, city="Imus"))
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("gcash-verify.ph", page)
        self.assertIn("no reportable domain", page)
        self.assertNotIn("rows are demo data", page)

    def test_rejects_container_and_null_controlled_values(self):
        for field in ("predicted_class", "city", "brand"):
            for value in ([], {}, None, True, 1):
                with self.subTest(field=field, value_type=type(value).__name__):
                    self.assert_rejected(app_payload(**{field: value}), field)

    def test_rejects_huge_and_infinite_scores(self):
        for score in (10 ** 400, float("inf"), float("-inf"), "0.5", None):
            self.assert_rejected(app_payload(score=score), "score")

    def test_date_offset_boundaries_and_overflow(self):
        for date in ("2026-01-01T00+14:01", "2026-01-01T00-14:59",
                     "2026-01-01T00+08:60", "0001-01-01T00+14:00",
                     "9999-12-31T23-14:00", "2026-01-01T24Z"):
            self.assert_rejected(app_payload(date_hour=date), "hour-only")
        for offset in ("+14:00", "-14:00", "+05:30", "+05:45"):
            self.assertEqual(self.post(app_payload(date_hour="2026-01-01T12" + offset)).status_code, 201)

    def test_identifier_keys_rejected_without_reflection_or_logging(self):
        from unittest.mock import patch
        marker = "SYNTHETIC_REJECTED_BODY_MARKER"
        with patch.object(backend.app.logger, "error") as error, patch.object(backend.app.logger, "info") as info:
            for field in ("phone_number", "device_id", "sender", "message_text", marker):
                response = self.post(app_payload(**{field: marker}))
                self.assertEqual(response.status_code, 400)
                self.assertNotIn(marker, response.get_data(as_text=True))
            error.assert_not_called()
            info.assert_not_called()

    def test_unicode_auth_header_rejected_without_server_error(self):
        backend.AUTH_TOKEN = "synthetic-token"
        self.assertEqual(self.post(app_payload(), headers={"Authorization": "Bearer ñ"}).status_code, 401)

    def test_demo_and_reports_have_separate_aggregates(self):
        import seed
        self.post(app_payload(domain="fixture-real.ph"))
        seed.main()
        seed.main()
        from flask import template_rendered
        contexts = []
        def capture(sender, template, context, **extra):
            contexts.append(context)
        with template_rendered.connected_to(capture, backend.app):
            self.client.get("/")
            self.client.get("/?demo=1")
        self.assertEqual(contexts[0]["total"], 1)
        self.assertEqual(contexts[0]["demo_count"], 0)
        self.assertEqual(contexts[1]["total"], seed.N_ROWS)
        self.assertEqual(contexts[1]["demo_count"], seed.N_ROWS)
        self.assertNotIn("fixture-real.ph", str(contexts[1]["recent"]))

    def test_dashboard_has_no_external_resources(self):
        page = self.client.get("/").get_data(as_text=True)
        self.assertNotIn('href="https://', page)
        self.assertNotIn('src="https://', page)

    def test_contract_matches_android_controlled_values(self):
        from pathlib import Path
        import re
        source = (Path(__file__).resolve().parents[1] / "android/app/src/main/java/ph/smishguard/privacy/Reports.kt").read_text(encoding="utf-8")
        for enum, values, excluded in (("City", backend.CITIES, "Not selected"),
                                       ("Brand", backend.BRANDS, "Not specified")):
            line = next(line for line in source.splitlines() if line.startswith("enum class " + enum))
            self.assertEqual(set(re.findall(r'\("([^"]+)"\)', line)) - {excluded}, values)
        suffix_line = next(line for line in source.splitlines() if "private val suffixes" in line)
        self.assertEqual(set(re.findall(r'"([^"]+)"', suffix_line)), backend.DOMAIN_SUFFIXES)


class SeedTest(unittest.TestCase):

    def test_seed_rows_pass_validation_and_are_labelled(self):
        import seed
        seed.main()
        page = backend.app.test_client().get("/?demo=1").get_data(as_text=True)
        self.assertIn("rows are demo data", page)
        conn = sqlite3.connect(backend.DB_PATH)
        n_demo = conn.execute("SELECT COUNT(*) FROM reports WHERE is_demo = 1").fetchone()[0]
        bad = conn.execute("SELECT COUNT(*) FROM reports WHERE is_demo = 1 "
                           "AND domain IS NOT NULL AND domain NOT LIKE '%demo%'").fetchone()[0]
        conn.close()
        self.assertEqual(n_demo, seed.N_ROWS)
        self.assertEqual(bad, 0, "every demo domain must contain 'demo'")


if __name__ == "__main__":
    unittest.main()
