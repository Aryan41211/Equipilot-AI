# EquiPilot AI — Citation Audit

**Project:** EquiPilot AI  
**Date:** 2026-11-24  
**Git SHA:** `0fccaca`

---

## Citation Structure

Each citation returned by SynthesisAgent contains:

| Field | Type | Description |
|-------|------|-------------|
| id | int | Unique citation identifier |
| type | string | `market_data`, `news`, or `sentiment` |
| title | string | Citation title |
| source | string | Data source (yfinance, NewsAPI, etc.) |
| url | string | Source URL |
| chunk_text | string | Relevant text excerpt |
| confidence | float | Confidence score 0.0-1.0 |

---

## Citation Flow

1. **SynthesisAgent.generate_report()** calls LLM with market data, news, sentiment
2. LLM returns `SynthesizedReport` with `market_data_sources`, `news_sources`, `sentiment_sources`
3. **synthesis_node** converts these to citation dicts
4. Citations are included in API response

---

## Current Status

| Aspect | Status | Details |
|--------|--------|---------|
| OPENAI_API_KEY | Not configured | LLM calls fail, fallback to placeholder |
| Citations generated | No | Placeholder report has no citations |
| Citation precision | Not measured | No citations to evaluate |
| Citation coverage | Not measured | No citations to evaluate |
| Citation-source alignment | Not measured | No citations to evaluate |

---

## Citation Integrity Rules

1. **A citation must support the claim it accompanies** — Each citation's `chunk_text` should contain evidence for the associated report statement
2. **No fabricated citations** — All citations must point to actual data sources retrieved during the graph execution
3. **Source attribution** — Each citation includes source name and URL for verification
4. **Confidence scoring** — Each citation has a confidence score (0.0-1.0)

---

## Recommendations

1. Configure `OPENAI_API_KEY` to enable LLM-based synthesis and citation generation
2. Create a citation audit dataset with 50+ report-citation pairs
3. Implement automated citation-source verification (check that citation URLs are accessible)
4. Add citation precision/coverage metrics to the evaluation pipeline
