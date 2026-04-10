---
dun:
  id: FEAT-004
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-004 -- Funder Report Generation

**Feature ID**: FEAT-004
**Status**: Draft
**Priority**: P0
**Owner**: Core Engineering

## Overview

Funder report generation auto-produces structured restoration progress reports from monitored data, eliminating the 2-3 days of manual assembly currently required per quarterly report. This feature implements PRD P0-4 and is identified in the seed strategy as the likely "first killer feature" because it delivers immediate, tangible time savings to the economic buyer (program managers who write grant reports).

## Problem Statement

- **Current situation**: Watershed program managers manually assemble quarterly funder reports by exporting iNaturalist data, pulling water quality readings, reviewing field notes, creating charts in Excel, and writing narrative summaries. Each report takes 2-3 analyst-days. Reports for OWEB (Oregon Watershed Enhancement Board) require specific sections: intervention timeline, outcome indicators, before/after comparisons, and narrative progress assessment.
- **Pain points**: Report assembly is the single largest administrative time sink for program managers; report quality varies based on who writes it; before/after comparisons require manually locating and aligning data from different periods and sources; narrative sections are written from scratch each quarter rather than building on prior reports; when a manager leaves, the next person has no template for how outcomes were previously characterized.
- **Desired outcome**: A manager selects a site, date range, and report type, and receives a draft report within 5 minutes containing all required sections populated from monitored data -- ready for human review and minor edits before submission.

## Requirements

### Functional Requirements

1. Given a site, date range, and report format (initially: OWEB quarterly progress), the system generates a complete structured report
2. Reports include an executive summary (2-3 paragraphs) synthesizing key outcomes and status for the period
3. Reports include an intervention timeline showing all logged actions within the reporting period with dates, locations, and descriptions
4. Reports include a before/after indicator species table comparing detection status of restoration-relevant taxa between the baseline period and the current reporting period
5. Reports include water quality trend charts (dissolved oxygen, temperature, and any additional configured parameters) for the reporting period with comparison to prior periods
6. Reports include an outcome KPI scorecard with targets vs. actuals for metrics defined in the site's restoration plan (e.g., native species richness target: 50 taxa, actual: 43)
7. Reports include a confidence assessment narrative explaining the strength of evidence for reported outcomes and flagging where data gaps limit conclusions
8. All data elements in the report are linked to source records; hovering or clicking a statistic shows the underlying observations or readings
9. Reports are exportable as PDF (formatted for print/submission) and Markdown (for version control and editing)
10. Reports include auto-generated maps showing observation density, species detection locations, and intervention zones within the site boundary
11. Users can edit any section of the generated report text in a rich-text editor before export, without breaking data linkages in unedited sections
12. The system stores generated reports and supports versioning (draft, reviewed, final)

### Non-Functional Requirements

- **Performance**: Report generation completes within 5 minutes for sites with up to 1,000 observations and 3 years of intervention history
- **Accuracy**: Fewer than 5% of data points in generated reports are incorrect when verified against source data (measured by domain advisor spot-check during pilot)
- **Format compliance**: Generated OWEB reports pass format review by pilot customer without structural revision (section order, required elements present)

## User Stories

- US-010 -- Manager generates quarterly OWEB progress report (to be created in `docs/helix/01-frame/user-stories/`)
- US-011 -- Manager edits generated report narrative before submission (to be created)
- US-012 -- Grant manager compares reports across funded sites (to be created)

## Edge Cases and Error Handling

- **Incomplete data coverage**: If the reporting period has gaps (e.g., no water quality data for 1 of 3 months), the report explicitly notes the gap in each affected section and in the confidence assessment, rather than silently omitting the period
- **No prior period for comparison**: If this is the first report for a new site, before/after tables show "Baseline -- no prior comparison available" and the executive summary frames this as an initial assessment
- **Large observation volume**: If the site has >1,000 observations in the reporting period, the report summarizes by taxonomic group and highlights notable detections rather than listing all observations
- **User edits break data consistency**: If a user edits a numeric value in the report that was sourced from data (e.g., changes species count), the system flags the edit with a visual indicator showing the original data-sourced value alongside the user's override

## Success Metrics

- Report generation time under 5 minutes (vs. baseline 2-3 analyst-days)
- At least 1 quarterly report submitted to a funder using RiverSignal output during the pilot
- Pilot users rate report quality at 4+ out of 5 for accuracy and completeness
- Fewer than 3 structural revisions required to meet OWEB format requirements per report

## Constraints and Assumptions

- Assumes OWEB quarterly report format requirements are documented and stable; format changes require template updates
- Assumes the site has sufficient observation and intervention data to populate all required report sections; the system cannot generate meaningful reports for sites with no monitoring data
- PDF generation from structured data and maps requires a rendering service; assumes server-side PDF generation is feasible within the 5-minute performance target

## Dependencies

- **Other features**: FEAT-001 (Observation Interpretation) provides ecological summaries that inform the executive summary and outcome narrative; FEAT-002 (Restoration Forecasting) provides forecast vs. actuals data for outcome scoring; FEAT-005 (Data Ingestion) provides all source data; FEAT-006 (Map Workspace) provides map rendering for report maps
- **External services**: Anthropic Claude API for narrative generation; PDF rendering service
- **PRD requirements**: Implements P0-4 (Funder report generation)

## Out of Scope

- Multi-funder report formats in MVP (only OWEB initially; NOAA, BPA, tribal formats are P2)
- Automated report submission to funder portals (reports are downloaded and submitted manually)
- Financial reporting (budget expenditure, cost-per-outcome calculations)
- Report comparison analytics across multiple sites or organizations (covered by P1-3 multi-site dashboard)

## Review Checklist

- [x] Overview connects this feature to a specific PRD requirement
- [x] Problem statement describes what exists now and what is broken -- not just what is wanted
- [x] Every functional requirement is testable -- you can write an assertion for it
- [x] Non-functional requirements have specific numeric targets, not "must be fast"
- [x] Edge cases cover realistic failure scenarios, not just happy paths
- [x] Success metrics are specific to this feature, not product-level metrics
- [x] Dependencies reference real artifact IDs (FEAT-XXX, external APIs)
- [x] Out of scope excludes things someone might reasonably assume are in scope
- [x] No implementation details ("use X library", "create Y table") -- specify WHAT not HOW
- [x] Feature is consistent with governing PRD requirements
- [x] No [NEEDS CLARIFICATION] markers remain unresolved for P0 features
