"""
Fills the dashboard with DEMO rows so it has something to show.

    python seed.py

No dataset is read. Every row is invented, marked is_demo=1 in the database,
and labelled "demo" on the dashboard. Domains all contain "demo" so no row can
be mistaken for a real report. Re-running replaces demo rows only; real
reports are never touched.
"""

import random
import sqlite3
from datetime import datetime, timedelta, timezone

import app as backend

BRAND_DOMAINS = {
    "BDO":    ["bdo-demo-alert.com", "demo-bdo-rewards.ph"],
    "BPI":    ["bpi-demo-secure.com", "demo-bpi-cancel.net"],
    "GCash":  ["gcash-demo-verify.ph", "demo-gcash-promo.com"],
    "Maya":   ["maya-demo-claim.com"],
    "SSS":    ["sss-demo-loan.com.ph"],
    "Other financial institution": ["demo-bank-notice.net"],
}
CITY_WEIGHTS = {"Dasmariñas": 6, "Bacoor": 3, "Imus": 3, "Manila": 2, "Other city": 1}
PHT = timezone(timedelta(hours=8))
N_ROWS = 120


def main():
    backend.init_db()
    rng = random.Random(42)
    now = datetime.now(PHT).replace(minute=0, second=0, microsecond=0)
    cities = list(CITY_WEIGHTS)
    brands = list(BRAND_DOMAINS)

    rows = []
    for _ in range(N_ROWS):
        local = now - timedelta(hours=rng.randint(0, 24 * 30))
        suspicious = rng.random() < 0.85
        brand = rng.choice(brands) if rng.random() < 0.8 else None
        if brand and rng.random() < 0.8:
            domain = rng.choice(BRAND_DOMAINS[brand])
        else:
            domain = None   # no reportable domain
        score = rng.uniform(0.52, 0.98) if suspicious else rng.uniform(0.05, 0.49)
        payload = {
            "domain": domain,
            "score": round(score, 4),
            "predicted_class": "suspicious" if suspicious else "not_suspicious",
            "date_hour": local.strftime("%Y-%m-%dT%H") + "+08:00",
            "city": rng.choices(cities, weights=list(CITY_WEIGHTS.values()))[0],
        }
        if brand:
            payload["brand"] = brand
        # Demo rows pass through the same validator as real ones.
        record, error = backend.validate(payload)
        if error:
            raise SystemExit(f"demo row failed validation: {error}\n{payload}")
        rows.append(record)

    conn = sqlite3.connect(backend.DB_PATH)
    conn.execute("DELETE FROM reports WHERE is_demo = 1")
    conn.executemany(
        "INSERT INTO reports (domain, score, predicted_class, date_hour, hour_utc, "
        "city, brand, is_demo) VALUES (:domain, :score, :predicted_class, "
        ":date_hour, :hour_utc, :city, :brand, 1)",
        rows,
    )
    conn.commit()
    conn.close()
    print(f"Seeded {len(rows)} DEMO rows into {backend.DB_PATH.name}")


if __name__ == "__main__":
    main()
