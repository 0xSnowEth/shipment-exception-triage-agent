# Logistics Shipment Exception Triage Agent

LangGraph/LangChain prototype for triaging logistics shipment exceptions with a supervisor-subagent architecture, deterministic tools, mock operational data, evidence logging, and human approval before customer-facing action.

Demo video:
https://app.airtimetools.com/recorder/s/z_NSSd9oVPB3Err7TkVN1W

## Problem

Logistics operators often triage shipment exceptions manually across carrier tracking, customer records, SLA rules, and internal communication channels. This creates slow response times, inconsistent escalation decisions, and risky customer updates when evidence is incomplete.

This prototype focuses on one narrow workflow:

```text
shipment exception input
-> load shipment record
-> classify exception
-> assess ETA/SLA/value/customer risk
-> inspect carrier tracking
-> choose resolution route
-> draft customer-safe update
-> save evidence
-> require human approval before customer-facing action
```

## Architecture

Graph ID:

```text
shipment_exception_supervisor
```

Main graph:

```text
agents.py:shipment_exception_supervisor
```

Supervisor responsibilities:

- load the shipment record first
- delegate independent analysis to subagents
- combine evidence into a final route and summary
- save audit artifacts
- pause for human approval before mock-sending a customer update

Subagents:

- `exception_classifier_agent`: normalizes carrier exception codes and classifies the business exception type
- `impact_assessment_agent`: evaluates ETA delta, SLA risk, shipment value risk, and severity
- `carrier_status_agent`: inspects tracking history, stale tracking, missing POD, and carrier follow-up needs
- `customer_risk_agent`: checks customer tier, complaints, SLA exposure, and notification risk
- `resolution_planner_agent`: chooses operational route and next action
- `communication_draft_agent`: drafts customer-safe and internal messages
- `evidence_report_agent`: saves final triage and evidence logs

Human-in-the-loop boundary:

- `mock_send_customer_update` interrupts before writing the approved customer update
- resume with `"approve"` in LangGraph Studio to approve the mock send
- approved sends are written to `outputs/approved_customer_updates.json`

## Repository Map

```text
agents.py                     supervisor and subagent wrappers
tools.py                      deterministic tools and mock persistence actions
langgraph.json                LangGraph graph export config
.env.example                  environment variable template
mock_data/shipments.json      source shipment records
mock_data/tracking_events.json mock carrier tracking events
mock_data/customers.json      mock customer/account records
mock_data/sla_rules.json      mock SLA rules
outputs/                      generated triage/evidence artifacts
manual_workflow.md            manual process being automated
test_cases.md                 normal, messy, ambiguous, and HITL test cases
evidence_log.md               human-readable run evidence
failure_notes.md              bad outputs, fixes, and retests
what_stays_human.md           human approval boundaries
ai_usage.md                   AI usage disclosure
SUBMISSION.md                 challenge-style written response
```

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env` with the Bedrock credentials required by `ChatBedrock`:

```text
AWS_BEARER_TOKEN_BEDROCK=your_token_here
```

## Run

Validate the graph:

```bash
langgraph validate
```

Start the local LangGraph server:

```bash
langgraph dev
```

Open the Studio URL printed by the command and select:

```text
shipment_exception_supervisor
```

## Demo Prompts

Clean delay case:

```text
Triage shipment SHP-1001 using the mock data. Classify the exception, assess ETA/SLA/customer risk, inspect tracking, choose the route, draft a customer-safe update, save the evidence, and tell me whether human review is required.
```

Messy delivery dispute with HITL approval:

```text
Shipment SHP-1002 has carrier marked delivered, but customer says not received.
POD is missing.
Customer has recent delivery complaints.

Triage the shipment using the mock data. Classify the exception, assess ETA/SLA/customer risk, inspect tracking, choose the route, draft a customer-safe update, save the evidence, and then attempt to send the customer update through the approved customer update tool.
```

When the HITL interrupt appears, resume with:

```json
"approve"
```

Ambiguous missing-data case:

```text
Shipment SHP-1003 has missing promised delivery and unknown customer tier.
Tracking has no new scan after pickup.
```

## Expected Artifacts

Successful runs create or update:

```text
outputs/triage_results.json
outputs/evidence_log.jsonl
outputs/approved_customer_updates.json
```

The repo also includes human-readable evidence and failure analysis:

```text
evidence_log.md
failure_notes.md
```

## Safety Boundaries

The agent may draft, classify, score, recommend, and save evidence.

The agent must not autonomously approve refunds, credits, replacements, reships, carrier claims, financial remedies, or customer-facing messages. Customer-facing updates are gated through HITL approval.

## Known Limitations

- Uses mock logistics data instead of live TMS, carrier, CRM, or email integrations.
- Uses a mock customer update tool instead of real email sending.
- Does not include production authentication or role-based permissions.
- Some business thresholds are simplified for demo clarity.
- LangSmith is used for trace review/observability, not as a full automated evaluation suite in this prototype.
