# MedEvidence Demo Release Acceptance

## Release Identity

- Date:
- Git commit:
- Workflow version: phase-6-v1
- Evaluation dataset version:
- Groundedness calibration version:
- Azure model deployment:
- Python version:
- Container image tag:

## Acceptance Gates

| Gate | Result | Evidence or notes |
| --- | --- | --- |
| Python source compiles | Pending | |
| Complete unit suite passes | Pending | |
| Golden-dataset gate passes | Pending | |
| Groundedness calibration gate passes | Pending | |
| LangSmith managed experiment reviewed | Pending | |
| Low-risk API response releases | Pending | |
| High-risk API response pauses for review | Pending | |
| Approved review resumes and releases | Pending | |
| Citation validation and release gate pass | Pending | |
| Uvicorn restart preserves checkpoint | Pending | |
| Container builds and becomes healthy | Pending | |
| Container replacement preserves checkpoint | Pending | |
| GitHub CI checks pass | Pending | |
| `.env` is not tracked or copied into image | Pending | |

## Accepted Limitations

- Synthetic evidence only; not for clinical use.
- SQLite is a local single-instance durability demonstration.
- Authentication, authorization, APIM, PostgreSQL, real retrieval systems,
  managed identity, private networking, and formal GxP validation are production
  translations rather than demo claims.