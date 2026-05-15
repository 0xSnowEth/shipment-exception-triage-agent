# Business Test Cases

These are business-level tests for the LangGraph Studio demo. They are designed to prove normal handling, messy conflicting data, ambiguous missing data, and human approval before customer-facing action.

## Test Case 1: Clean Delay Case

Input:

```text
Triage shipment SHP-1001 using the mock data. Classify the exception, assess ETA/SLA/customer risk, inspect tracking, choose the route, draft a customer-safe update, save the evidence, and tell me whether human review is required.
```

Expected behavior:

```text
The supervisor calls load_shipment_record first.
The agent uses Northstar Medical Supplies, $48,000, expedited service, $5,000 SLA penalty, medical devices, promised delivery 2026-05-15T17:00:00+00:00, and current ETA 2026-05-16T11:00:00+00:00.
The exception is classified as a delay.
The route includes carrier follow-up and human escalation.
Human review is required.
Customer update is drafted but not sent automatically.
Evidence is saved to outputs/.
```

What this proves:

```text
The agent uses source-of-truth mock data instead of inventing shipment facts.
```

## Test Case 2: Messy Conflicting Data Case

Input:

```text
Shipment SHP-1002 has carrier marked delivered, but customer says not received.
POD is missing.
Customer has recent delivery complaints.
```

Expected behavior:

```text
The supervisor calls load_shipment_record first.
The exception is treated as delivery dispute / lost or missing shipment.
The agent does not claim delivery was confirmed.
Evidence mentions missing POD, customer dispute, sparse tracking, priority customer, and open complaint.
The route includes lost shipment investigation and human escalation.
Human review is required.
Customer update is drafted but not sent automatically.
Evidence is saved to outputs/.
```

What this proves:

```text
The agent handles contradictory carrier/customer evidence instead of trusting the carrier scan blindly.
```

## Test Case 3: Failure / Ambiguous Missing-Data Case

Input:

```text
Shipment SHP-1003 has missing promised delivery and unknown customer tier.
Tracking has no new scan after pickup.
```

Expected behavior:

```text
The supervisor calls load_shipment_record first.
The agent does not invent promised delivery, SLA penalty, or customer tier.
The agent states which fields are missing.
ETA/SLA risk is marked unknown or indeterminate where required fields are missing.
The route includes lost shipment investigation or human escalation because tracking visibility is poor.
Human review is required.
Evidence is saved to outputs/.
```

What this proves:

```text
The agent escalates ambiguous data instead of silently guessing.
```

## Test Case 4: Human-In-The-Loop Customer Update

Input:

```text
Shipment SHP-1002 has carrier marked delivered, but customer says not received.
POD is missing.
Customer has recent delivery complaints.

Triage the shipment using the mock data. Classify the exception, assess ETA/SLA/customer risk, inspect tracking, choose the route, draft a customer-safe update, save the evidence, and then attempt to send the customer update through the approved customer update tool.
```

Expected behavior:

```text
The supervisor completes the SHP-1002 triage.
The customer-safe update is drafted.
The evidence report is saved.
The supervisor calls mock_send_customer_update.
The graph interrupts before the mock customer update is sent.
The human resumes with "approve".
Only after approval does outputs/approved_customer_updates.json receive the approved mock-send record.
The final answer says financial remedies, claims, replacements, credits, and reships are pending human authorization only.
```

What this proves:

```text
The agent can pause before a customer-facing action and continue only after human approval.
```
