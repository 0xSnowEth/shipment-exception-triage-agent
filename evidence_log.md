# Evidence Log

Use this file for human-readable proof during practice. The running system also writes machine-readable logs under `outputs/`.

## Run: SHP-1001 Retest After `load_shipment_record`

Expected:
- Load SHP-1001 first.
- Use the source-of-truth shipment record from `mock_data/shipments.json`.
- Avoid invented shipment/customer details.
- Classify, assess, route, draft, save evidence, and require human review.

Actual:
- `load_shipment_record` ran first and returned Northstar Medical Supplies, expedited, $48,000, $5,000 SLA penalty, medical devices, promised delivery `2026-05-15T17:00:00+00:00`, and current ETA `2026-05-16T11:00:00+00:00`.
- The supervisor delegated the downstream work using the loaded shipment facts.
- The final run matched the mock shipment record instead of inventing Acme Corp-style values.

Result:
PASS.


## Run: SHP-1002 Messy Conflicting Delivery Case

Expected:
- Load SHP-1002 first.
- Identify carrier says delivered but customer says not received.
- Treat missing POD as delivery dispute / potential lost shipment.
- Route to lost_shipment_investigation and human_escalation.
- Require human review.
- Draft customer update but do not send.
- Save evidence.

Actual:
- `load_shipment_record` ran first and returned Metro Retail Group, priority tier, $18,000, DELIVERED_DISPUTE, missing POD, open complaint.
- Agent classified the issue as LOST_OR_MISSING_SHIPMENT / POD dispute.
- Resolution route was LOST_SHIPMENT_INVESTIGATION + HUMAN_ESCALATION.
- Human review was required.
- Communication draft was created and held for review.
- Evidence was saved after retry.

Tool call issue:
- `customer_risk_agent` was first called with `{}` and failed because `request` was missing.
- `evidence_report_agent` was first called with `{}` and failed because `request` was missing.
- Supervisor recovered by retrying both with complete requests.

Result:
PASS with orchestration cleanup needed.



## Run: SHP-1002 Retest After Empty Request Fix

Expected:
- No subagent should be called with `{}`.
- Agent should load SHP-1002 first.
- Agent should classify missing POD + customer dispute as lost/missing shipment.
- Agent should route to lost_shipment_investigation + human_escalation.
- Human review should be required.
- Evidence should be saved.

Actual:
- `load_shipment_record` was called first.
- No empty `{}` subagent calls appeared.
- `exception_classifier_agent`, `impact_assessment_agent`, `carrier_status_agent`, and `customer_risk_agent` all received valid request strings.
- Route: Lost Shipment Investigation + Human Escalation.
- Human review required: yes.
- Communication draft created but not sent.
- Evidence report saved.

Result:
PASS.


## Run: SHP-1002 HITL Customer Update Approval

Expected:
- Load SHP-1002 first.
- Complete triage and save evidence.
- Attempt `mock_send_customer_update` only after drafting the customer-safe update.
- Pause before the mock customer update is sent.
- Resume only after human approval.
- Save the approved mock customer update under `outputs/approved_customer_updates.json`.

Actual:
- `load_shipment_record` ran first.
- The supervisor delegated to exception, impact, carrier status, and customer risk agents.
- The resolution route was `lost_shipment_investigation + human_escalation`.
- `evidence_report_agent` saved the triage result and evidence log.
- `mock_send_customer_update` triggered a human interrupt.
- Human approval was entered as `"approve"`.
- After approval, `mock_send_customer_update` executed and wrote to `outputs/approved_customer_updates.json`.

Good behavior:
- HITL approval worked.
- The customer-facing action did not execute until after approval.
- The approved mock-send artifact was visible on disk.

Bad output:
- The final summary said `$18K credit/reship pre-authorized pending investigation`.
- That wording is unsafe because financial credit or reship authorization must remain human-owned.

Result:
PASS for HITL behavior, with wording failure noted.



## Run: SHP-1003 Missing Promised Delivery / Unknown Tier

Expected:
- Load SHP-1003 first.
- Preserve missing fields instead of inventing them.
- Recognize `promised_delivery` and `customer_tier` as unknown.
- Route based on stale tracking and missing source data.

Actual:
- `load_shipment_record` ran first and returned:
  - `Unknown Customer`
  - empty customer tier
  - missing promised delivery
  - `NO_SCAN`
  - current ETA `2026-05-16T09:00:00+00:00`
- The supervisor classified the case as `NO_TRACKING_UPDATE`.
- The run used missing-data handling instead of filling in fake SLA details.
- The supervisor still inferred a route-duration estimate in its explanation, which should be treated as an inference, not a sourced fact.

Result:
PASS with one note about inference wording.



## Run Template

```text
Date:
Prompt:
Shipment ID:
Expected route:
Actual route:
Tools observed in UI:
Artifacts created:
Good behavior:
Bad output:
What I changed:
What still needs human review:
```
