"""Refresh public-source replay payloads without mixing partial loads into analytics."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from .run import FIXTURES
from .sources import SNAPSHOT_DATE, validate_source_payload


SOURCES = {
    "eurostat_unemployment.json": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?geo=BG&geo=EL&geo=IE&geo=IT&geo=PL&geo=RO&sex=T&age=TOTAL&unit=PC_ACT&s_adj=SA",
    "eurostat_job_vacancy.json": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/jvs_q_nace2?geo=BG&geo=EL&geo=IE&geo=IT&geo=PL&geo=RO&s_adj=NSA&nace_r2=A-S&sizeclas=TOTAL&indic_em=JVR",
    "world_bank_inflation.json": "https://api.worldbank.org/v2/country/BGR;GRC;IRL;ITA;POL;ROU/indicator/FP.CPI.TOTL.ZG?format=json&per_page=1000",
}


def refresh() -> int:
    """Fetch every source to a staging directory, then atomically replace successes."""
    raw_dir = FIXTURES / "raw"
    staging = raw_dir / ".staging"
    staging.mkdir(parents=True, exist_ok=True)
    report_path = raw_dir / "source_refresh_report.json"
    previous = json.loads(report_path.read_text()) if report_path.exists() else {}
    access_dates = {item["file"]: item.get("snapshot_accessed_at", SNAPSHOT_DATE) for item in previous.get("sources", [])}
    report = {"accessed_at": datetime.now(UTC).isoformat(), "sources": []}
    for filename, url in SOURCES.items():
        try:
            request = Request(url, headers={"User-Agent": "asteria-retention-signals/0.1"})
            with urlopen(request, timeout=30) as response:
                payload = response.read()
            validate_source_payload(filename, json.loads(payload))
            staged = staging / filename
            staged.write_bytes(payload)
            staged.replace(raw_dir / filename)
            report["sources"].append({"file": filename, "url": url, "status": "refreshed", "snapshot_accessed_at": report["accessed_at"], "sha256": hashlib.sha256(payload).hexdigest()})
            print(f"Refreshed {filename}")
        except (URLError, TimeoutError, ValueError, OSError, KeyError, TypeError, IndexError) as error:
            report["sources"].append({"file": filename, "url": url, "status": "retained_previous_fixture", "snapshot_accessed_at": access_dates.get(filename, SNAPSHOT_DATE), "error": str(error)})
            print(f"Could not refresh {filename}; retained the previous replay fixture: {error}")
    (raw_dir / "source_refresh_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    failures = [source for source in report["sources"] if source["status"] != "refreshed"]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(refresh())
