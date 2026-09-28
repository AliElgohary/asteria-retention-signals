# Source register

The pipeline uses saved replay fixtures for offline, deterministic review, with an optional refresh command for live retrieval.

| Provider | Indicator | Lens | Frequency | Canonical unit | Intended coverage | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Eurostat | Unemployment rate (`une_rt_m`) | Labour supply | Monthly | Percent of labour force | Six assessment countries | Replay fixture captured 2026-09-25 |
| Eurostat | Job vacancy rate (`jvs_q_nace2`) | Labour demand | Quarterly | Percent | Six assessment countries where reported | Replay fixture captured 2026-09-25 |
| World Bank | Inflation, consumer prices (`FP.CPI.TOTL.ZG`) | Cost-of-living pressure | Annual | Annual percent change | Six assessment countries | Replay fixture captured 2026-09-25 |

The raw public payloads are preserved in `data/fixtures/raw/`, with access date 2026-09-25. The adapter selects total sex, the `TOTAL` age category, percentage of active population, seasonally adjusted values for unemployment; whole economy, total enterprise size, job vacancy rate, not seasonally adjusted for vacancies; and the World Bank national annual inflation series. An estimated availability rule (45 days monthly, 90 days quarterly, 120 days annual) prevents a signal from joining a metric before its assumed publication date. This is a documented approximation, not a historical vintage dataset. Eurostat data reuse follows its [copyright notice](https://ec.europa.eu/info/legal-notice_en#copyright-notice); the World Bank indicator is published under [CC BY 4.0](https://datahelpdesk.worldbank.org/knowledgebase/articles/902061).

## Verified replay coverage and contracts

The replay contains 450 non-null observations: 360 unemployment observations (60 months × six markets), 60 vacancy observations (20 quarters × BG/PL/RO), and 30 inflation observations (five years × six markets). Although six geographies are requested for vacancies, the selected `A-S` series has no usable observations for GR, IE or IT in the retained horizon. Missing observations are not filled with zero. Annual observations remain annual, and 2025 inflation cannot join a 2025 outcome under the 120-day rule.

The exact requested series are recorded in `src/asteria_retention/ingest_external.py`. For unemployment the saved payload uses `age=TOTAL`, `sex=T`, `unit=PC_ACT`, `s_adj=SA`, `freq=M`; the canonical adapter verifies these codes. Vacancy uses `nace_r2=A-S`, `sizeclas=TOTAL`, `indic_em=JVR`, `s_adj=NSA`, `freq=Q`. Inflation uses `FP.CPI.TOTL.ZG`, national annual percent change. Eurostat `EL` maps to `GR`, and World Bank ISO3 country codes map explicitly to the six ISO2 workforce codes.

Unemployment measures labour supply conditions, vacancies indicate demand for labour, and inflation represents household cost-of-living pressure. National measures cannot describe Asteria's precise occupations, locations, wages or hiring competition. Vacancy coverage is an explicit tradeoff: the narrow series remains comparable where available, but reduces association samples to three countries.

Each snapshot refresh validates structure, indicator/dimension selection, finite observations in the target horizon and World Bank pagination before replacing a file. Failures retain the previous usable payload and its access time; source failures are independent and return a nonzero exit code. Eurostat status flags are carried through as quality lineage without assuming that provisional or estimated values are final. Provider update metadata and snapshot load times remain separate from the assumed publication date.

Terms checked during the review on 2026-09-28: [Eurostat reuse and attribution notice](https://ec.europa.eu/eurostat/web/main/help/copyright-notice), and [World Bank indicator, attribution and CC BY 4.0 licence](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG). The World Bank publishes this series with attribution to the IMF International Financial Statistics database. This product selects and transforms Eurostat data; its analysis and interpretations are the author's responsibility, not Eurostat's.

The saved fixtures retain their original capture date at day-level precision; successful new refreshes record UTC timestamps. Offline runs use these fixtures without contacting the providers. Historical revisions mean that publication-lag estimates cannot establish whether the precise values were available to decision makers at the time.
