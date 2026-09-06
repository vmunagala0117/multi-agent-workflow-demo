## Baseline Results

Copy the aggregate values from the completed LangSmith experiment. Do not
estimate or round away failures.

| Metric | Baseline value | Gate type |
| --- | ---: | --- |
| `release_status_match` | `<value>` | Hard |
| `response_mode_match` | `<value>` | Hard |
| `validation_status_match` | `<value>` | Hard |
| `valid_citation_rate` | `<value>` | Hard |
| `overall_pass` | `<value>` | Hard |
| `groundedness_evaluated` | `<value>` | Hard |
| `grounded_claim_rate` | `<value>` | Review |
| `partial_or_better_rate` | `<value>` | Review |
| `no_unsupported_claims` | `<value>` | Hard |

## Groundedness Calibration Results

| Metric | Baseline value |
| --- | ---: |
| Calibration cases | `9` |
| Overall judge accuracy | `<value>` |
| Unsupported-claim recall | `<value>` |
| Unsupported → supported errors | `<value>` |

## Operational Observations

| Observation | Baseline |
| --- | --- |
| Unit-test result | `<passed count and date>` |
| Workflow trace errors | `<count>` |
| Approximate workflow latency | `<value>` |
| Approximate synthesis tokens/cost | `<value or not yet measured>` |
| Approximate judge calls per experiment | `<value>` |

## Promotion Decision

Decision: `<accepted as baseline / rejected>`

Rationale:

`<Brief evidence-based explanation, including any reviewed partial findings.>`

## Known Limitations

- The corpus and dataset are intentionally small and synthetic.
- The baseline does not establish clinical correctness or production safety.
- The groundedness judge is probabilistic and may share correlated errors with
  the synthesis model if the same deployment is used.
- Latency and cost thresholds require repeated runs and percentile analysis.
- Production labels require qualified reviewer governance and a holdout set.