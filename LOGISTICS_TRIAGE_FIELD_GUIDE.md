# Logistics Shipment Exception Triage Field Guide

Use this document to get operationally fluent enough to build the `Logistics Shipment Exception Triage Agent`. This is not a full logistics course. It only contains the concepts, data, workflow, and decision logic needed for the prototype.

## Why This Niche Is Worth Building

Logistics exception management is a strong agent workflow because the job is repetitive, time-sensitive, data-heavy, and still heavily manual.

Research signals:

- BCG reported in March 2026 that many logistics companies are still piloting AI, but few have embedded it into core logistics processes. The gap is not hype; it is operational execution. Source: https://www.bcg.com/publications/2026/ai-is-already-moving-the-logistics-industry-forward
- Redwood Logistics reported in May 2026 that only 13% of shippers deploying AI are generating quantifiable results. It also identified data quality and integration gaps across TMS, ERP, and planning tools as major blockers. Source: https://www.redwoodlogistics.com/insights/redwood-logistics-releases-ai-in-logistics-report-finding-only-13-percent-of-shippers-deploying-ai-are-generating-quantifiable-results
- Project44 launched an AI Ocean Exceptions Agent in 2026 for rolled-container disruptions, with humans still controlling rebooking and scheduling actions. Source: https://www.project44.com/press-releases/project44-launches-ai-ocean-exceptions-agent-to-autonomously-resolve-rolled-container-disruptions/
- Industry exception-management products focus on detecting ETA deviations, classifying disruptions, notifying customers, and rebooking alternatives. Source: https://www.lyzr.ai/ai-agents/ai-agents-for-shipment-exception-handling/

Translation: companies do not need "logistics ChatGPT." They need an operator that watches shipment exceptions, understands impact, routes the case, drafts communication, and escalates risky decisions.

## The One-Sentence Product

```text
An AI operations agent that triages delayed or disrupted shipments, checks order/carrier/customer impact, recommends the next action, drafts the customer update, and escalates SLA-risk cases to a human.
```

## Core Vocabulary

`Shipment`: A movement of goods from origin to destination.

`Carrier`: The company physically moving the shipment, such as FedEx, DHL, UPS, Maersk, a trucking carrier, or an ocean carrier.

`Shipper`: The business sending the goods.

`Consignee`: The receiver/customer getting the goods.

`3PL`: Third-party logistics provider. A company hired to manage logistics for another business.

`4PL`: Fourth-party logistics provider. A company that coordinates multiple logistics providers and systems at a higher orchestration level.

`TMS`: Transportation Management System. Software used to plan, execute, track, and optimize shipments. It often handles carrier selection, shipment tracking, freight cost, documents, and exception management. Sources: https://www.sap.com/canada/products/scm/transportation-logistics/what-is-a-tms.html and https://www.oracle.com/europe/scm/logistics/transportation-management/what-is-transportation-management-system/

`ERP`: Enterprise Resource Planning system. The business system that tracks orders, inventory, finance, purchasing, and operations.

`WMS`: Warehouse Management System. Software used to manage warehouse inventory, picking, packing, and shipping.

`ETA`: Estimated Time of Arrival.

`SLA`: Service Level Agreement. A promised service standard, such as delivery by a certain date/time.

`OTIF`: On Time In Full. A logistics KPI measuring whether an order arrived by the agreed date/window and in the complete expected quantity. Source: https://lot.dhl.com/glossary/on-time-in-full-otif/

`POD`: Proof of Delivery. Confirmation that shipment was delivered, often with signature, timestamp, photo, or delivery scan.

`Exception`: Anything that breaks the expected shipment plan.

## Common Shipment Exceptions

Your prototype should support these first:

```text
delay
missed_pickup
missed_delivery_window
address_issue
weather_delay
carrier_capacity_issue
customs_hold
damaged_goods
lost_or_missing_shipment
temperature_excursion
customer_refused_delivery
no_tracking_update
rolled_container
```

Do not implement all deeply at first. For Attempt 1, support:

```text
delay
missed_delivery_window
address_issue
damaged_goods
no_tracking_update
```

## The Human Manual Workflow

This is what a dispatcher, logistics coordinator, or operations analyst does manually:

```text
1. Check the shipment dashboard for exceptions.
2. Open the shipment details in the TMS.
3. Check order value, customer priority, delivery promise, carrier, route, and current ETA.
4. Check whether the shipment is already late or predicted to be late.
5. Check the exception reason from the carrier.
6. Compare the carrier reason against shipment history and tracking events.
7. Determine business impact: customer risk, SLA risk, inventory risk, production risk, or revenue risk.
8. Decide severity: low, medium, high, or critical.
9. Choose the route: wait, contact carrier, notify customer, expedite, rebook, file claim, or human escalation.
10. Draft a customer-safe update.
11. Escalate high-value, SLA-risk, damaged, lost, or ambiguous cases to a human.
12. Save the decision and evidence log.
```

## What The Agent Should Do

The agent should not "solve logistics." It should triage exceptions.

Minimum job:

```text
input shipment exception
-> classify exception type
-> inspect shipment/order/customer/carrier context
-> estimate severity
-> decide next route
-> draft customer/internal update
-> save evidence
-> escalate if risky or ambiguous
```

## Inputs You Need In Mock Data

Create fake JSON records with these fields:

```json
{
  "shipment_id": "SHP-1001",
  "order_id": "ORD-7721",
  "customer_name": "Northstar Medical Supplies",
  "customer_tier": "enterprise",
  "shipment_value_usd": 48000,
  "commodity": "medical devices",
  "origin": "Dallas, TX",
  "destination": "Phoenix, AZ",
  "carrier": "RoadFast Freight",
  "service_level": "expedited",
  "promised_delivery": "2026-05-15T17:00:00",
  "current_eta": "2026-05-16T11:00:00",
  "last_tracking_event": "Departed Dallas terminal",
  "last_tracking_time": "2026-05-14T08:30:00",
  "exception_code": "DELAY",
  "exception_message": "Mechanical delay at carrier terminal",
  "temperature_control_required": false,
  "customer_sla_penalty_usd": 5000,
  "open_customer_complaint": false
}
```

## Output Contract

Every processed exception should produce:

```json
{
  "shipment_id": "SHP-1001",
  "exception_type": "delay",
  "severity": "high",
  "route": "carrier_followup_and_customer_notice",
  "business_impact": "Misses promised delivery by 18 hours for enterprise customer with SLA penalty.",
  "recommended_action": "Contact carrier for recovery ETA and notify customer with revised delivery window.",
  "human_review_required": true,
  "evidence": [
    "Promised delivery: 2026-05-15 17:00",
    "Current ETA: 2026-05-16 11:00",
    "Customer tier: enterprise",
    "SLA penalty: $5000"
  ],
  "customer_update_draft": "We are tracking a carrier mechanical delay affecting your shipment...",
  "internal_note": "High SLA risk. Human should approve customer update before sending."
}
```

## Routing Logic

Use these routes:

```text
monitor_only
carrier_followup
customer_notice
expedite_review
rebook_review
address_correction_needed
damage_claim_review
lost_shipment_investigation
human_escalation
```

Simple route rules:

```text
If delay is under 2 hours and customer is not high priority -> monitor_only
If delay is over 4 hours -> carrier_followup
If promised delivery will be missed -> customer_notice
If customer tier is enterprise and SLA penalty exists -> human_escalation
If shipment is damaged -> damage_claim_review and human_escalation
If address is invalid -> address_correction_needed
If no tracking update for 24+ hours -> lost_shipment_investigation
If temperature controlled shipment has temperature issue -> human_escalation
```

## Severity Logic

Use this first-pass severity model:

```text
critical:
  high-value shipment, medical/perishable/temp-controlled goods, SLA penalty, lost shipment, damaged shipment, or customer production impact

high:
  promised delivery will be missed, enterprise customer, large delay, repeated exception, or open customer complaint

medium:
  delay likely recoverable but needs carrier follow-up

low:
  minor delay with no SLA or customer impact
```

## Human Approval Boundaries

The agent should not automatically do these:

```text
send customer-facing messages
approve refunds or credits
rebook shipment with extra cost
file claims with carriers
mark shipment lost
promise a delivery time not confirmed by carrier
change customer order data
```

The agent can safely:

```text
classify exception
score severity
draft messages
recommend route
save evidence log
prepare carrier follow-up questions
flag human review
```

## Ideal Supervisor/Subagent Design

Supervisor:

```text
shipment_exception_supervisor
```

Subagents:

```text
exception_classifier_agent:
  Turns raw carrier exception codes/messages into a clean exception type such as delay, address_issue, damaged_goods, or no_tracking_update.

impact_assessment_agent:
  Calculates how bad the exception is by comparing promised delivery, current ETA, shipment value, commodity risk, and SLA penalty.

carrier_status_agent:
  Reviews carrier/tracking data to understand what happened, whether tracking is stale, and what should be asked from the carrier.

customer_risk_agent:
  Checks customer importance, open complaints, SLA exposure, and whether the customer should be proactively notified.

resolution_planner_agent:
  Combines exception type, shipment impact, carrier status, and customer risk into the recommended route and next action.

communication_draft_agent:
  Drafts customer-safe updates and internal notes, but does not send anything automatically.

evidence_report_agent:
  Saves the final decision, reasoning, tool outputs, and proof points so the run can be audited later.
```

Each subagent should have real tools:

```text
shipment_exception_supervisor:
  load_shipment_record:
    Loads the full shipment record by shipment ID before delegating to subagents.
    Should include: shipment_id, found, shipment record or error. This is the source-of-truth tool that prevents the supervisor from inventing details.

exception_classifier_agent:
  normalize_exception_code:
    Converts messy carrier codes like DELAY_MECH, ADDR_ERR, or NO_SCAN into standard internal labels.
    Should include: raw exception code, raw exception message, carrier name, normalized code.

  classify_exception_type:
    Maps the normalized code/message to a business exception type.
    Should include: normalized code, exception message, final exception type, confidence, reason.

impact_assessment_agent:
  calculate_eta_delta:
    Compares promised delivery against current ETA to calculate lateness or early/on-time status.
    Should include: promised_delivery, current_eta, delta_hours, is_late.

  check_sla_breach:
    Determines whether the shipment is likely to violate a promised service level.
    Should include: promised_delivery, current_eta, service_level, customer_sla_penalty_usd, breach_risk.

  score_shipment_value_risk:
    Scores business impact from shipment value, commodity type, temperature control, and customer priority.
    Should include: shipment_value_usd, commodity, temperature_control_required, customer_tier, risk_score.

carrier_status_agent:
  get_tracking_history:
    Retrieves or reads the shipment's tracking events.
    Should include: shipment_id, event timestamps, event locations, event messages, latest event.

  detect_stale_tracking:
    Checks whether the shipment has gone too long without a tracking update.
    Should include: last_tracking_time, current_time, stale_threshold_hours, is_stale.

  prepare_carrier_followup:
    Creates the exact questions a human or system should ask the carrier.
    Should include: shipment_id, carrier, exception type, missing information, requested confirmation.

customer_risk_agent:
  lookup_customer_tier:
    Checks whether the customer is standard, priority, enterprise, strategic, or otherwise high value.
    Should include: customer_name, customer_id if available, customer_tier, account_owner.

  check_open_complaints:
    Checks whether the customer already has open issues related to this shipment or recent service failures.
    Should include: customer_name, shipment_id, open_complaints, complaint_summary.

  check_sla_penalty:
    Checks whether missing the promised delivery creates a contractual or financial penalty.
    Should include: customer_name, service_level, promised_delivery, penalty_amount, penalty_condition.

resolution_planner_agent:
  choose_resolution_route:
    Selects the operational route such as monitor_only, carrier_followup, customer_notice, damage_claim_review, or human_escalation.
    Should include: exception_type, severity, customer_risk, SLA risk, final route, reason.

  recommend_next_action:
    Produces the next practical action an operator should take.
    Should include: route, action owner, action text, urgency, human_review_required.

communication_draft_agent:
  draft_customer_update:
    Writes a customer-safe message explaining the issue without overpromising.
    Should include: customer_name, shipment_id, confirmed facts, revised ETA if confirmed, next step, review_required.

  draft_internal_note:
    Writes an internal operations note for the team handling the exception.
    Should include: shipment_id, severity, route, evidence, recommended action, unresolved questions.

evidence_report_agent:
  write_evidence_log:
    Records the key facts, tool outputs, decisions, assumptions, and source labels from the run.
    Should include: shipment_id, inputs reviewed, tool outputs, route, severity, assumptions, timestamp.

  save_triage_result:
    Saves the final structured triage result to a JSON file, database, or mock storage.
    Should include: shipment_id, exception_type, severity, route, human_review_required, evidence, drafts.
```

## Parallel Delegation Opportunities

This workflow naturally supports parallel subagent work.

Example:

```text
Supervisor receives shipment exception.

In parallel:
  carrier_status_agent checks tracking history.
  customer_risk_agent checks customer tier and SLA risk.
  impact_assessment_agent calculates ETA delta and business impact.

Then:
  resolution_planner_agent chooses route.
  communication_draft_agent drafts update.
  evidence_report_agent saves result.
```

This is stronger than the old lead-qualification prototype because multiple subagents can call multiple tools independently before the supervisor combines their results.

## Three Business Test Case Shapes

Do not write Python tests first. Write these business scenarios first.

Test Case 1: Clean delay case.

```text
Shipment is delayed 18 hours.
Enterprise customer.
SLA penalty exists.
Expected route: carrier_followup_and_customer_notice or human_escalation.
Expected human_review_required: true.
```

Test Case 2: Messy conflicting data case.

```text
Carrier says delivered.
Customer says not received.
POD is missing.
Tracking has no delivery scan.
Expected route: lost_shipment_investigation.
Expected human_review_required: true.
```

Test Case 3: Failure or ambiguous case.

```text
Shipment record is missing promised delivery date and customer tier.
Agent cannot calculate SLA risk.
Expected route: human_escalation.
Expected behavior: ask for missing fields instead of guessing.
```

## What Makes This Impressive

This workflow proves:

```text
multi-agent orchestration
parallel subagent delegation
real tools per subagent
structured output
routing logic
business impact scoring
human approval boundaries
evidence logging
failure handling
domain-specific reasoning
```

## What To Avoid

Avoid building:

```text
a chatbot that answers shipment questions
a generic customer support responder
a final summary with no tool evidence
a workflow that sends messages automatically
a system that guesses missing delivery dates
a demo with only one clean case
```

Avoid fake confidence:

```text
"This will reduce costs by 70%" without source labels.
"The carrier confirmed..." if the data is a stub.
"Shipment will arrive tomorrow" if no carrier-confirmed ETA exists.
```

## 60-Minute Learning Sprint

Spend one hour learning only this:

```text
10 minutes: TMS, ERP, WMS, carrier, shipper, consignee
10 minutes: ETA, SLA, OTIF, POD
10 minutes: common shipment exceptions
10 minutes: exception severity and customer impact
10 minutes: routing decisions and human approval
10 minutes: mock data fields and output contract
```

After that, start writing the manual workflow and three business test cases. Do not keep studying broadly.

## First Build Objective

Build a mock-data prototype, not a real carrier integration.

Files to create later:

```text
mock_data/shipments.json
mock_data/tracking_events.json
mock_data/customers.json
mock_data/sla_rules.json
test_cases.md
evidence_log.md
failure_notes.md
README.md
```

Your first target is one run that proves:

```text
shipment exception input
-> supervisor delegates to multiple subagents
-> subagents call tools
-> route and severity are calculated
-> customer update is drafted but not sent
-> evidence log is saved
-> human review is flagged when needed
```
