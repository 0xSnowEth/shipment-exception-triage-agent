# Challenge Submission: Intern 011 - Agentify It

Name: Ahmed Gamal, You can call me Harvey.

GitHub repo:
https://github.com/HarveyAGH/shipment-exception-triage-agent

Demo video:
https://app.airtimetools.com/recorder/s/z_NSSd9oVPB3Err7TkVN1W

Demo note:
The video is 7:06 because it includes the live LangGraph run, tool-call trace, human-in-the-loop approval, output artifacts, LangSmith trace proof, and failure notes. I kept the evidence complete rather than cutting core prototype proof.

## Part 1: Domain

Chosen domain: logistics operations.

The specific business pain point is shipment exception triage. Logistics teams deal with delays, missing scans, damaged goods, delivery disputes, missing proof of delivery, customer complaints, and SLA exposure. A human operator usually has to check multiple systems before deciding whether to monitor, contact a carrier, notify a customer, open an investigation, or escalate internally.

I chose this domain because the workflow is repetitive, evidence-heavy, and operationally risky. It is not enough for an agent to produce a nice answer; it must use source data, preserve uncertainty, save an audit trail, and stop before customer-facing or financial action.

I want to intern at Single Grain specifically because the brief describes the agency shifting from traditional services into tech-enabled services where AI agents handle repetitive work and humans focus on judgment. That is exactly the kind of environment I want to work in: fast shipping, practical automation, and real business workflows instead of theoretical AI demos.

The most impressive thing I have built so far is this working LangGraph/LangChain logistics triage prototype. It includes a supervisor-subagent architecture, deterministic tools, mock operational data, LangGraph Studio testing, LangSmith trace review, human-in-the-loop approval, output artifacts, and documented failures with retests.

## Part 2: Agentified Manual Workflow

Manual workflow:

```text
shipment exception input
-> open shipment record
-> inspect ETA, SLA, carrier, value, customer, and tracking context
-> classify exception
-> estimate severity
-> choose operational route
-> draft customer-safe update
-> save evidence
-> escalate risky or ambiguous cases to a human
```

Agent design:

```text
shipment_exception_supervisor
-> load_shipment_record
-> exception_classifier_agent
-> impact_assessment_agent
-> carrier_status_agent
-> customer_risk_agent
-> resolution_planner_agent
-> communication_draft_agent
-> evidence_report_agent
-> mock_send_customer_update with HITL approval
```

Tools and data:

```text
mock_data/shipments.json
mock_data/tracking_events.json
mock_data/customers.json
mock_data/sla_rules.json
outputs/triage_results.json
outputs/evidence_log.jsonl
outputs/approved_customer_updates.json
```

Human approval boundary:

```text
The agent may classify, score, draft, recommend, and save evidence.
The agent may not approve financial remedies, claims, replacements, reships, credits, refunds, or customer-facing sends without human approval.
```

Test cases:

```text
SHP-1001: clean carrier mechanical delay with SLA/customer risk.
SHP-1002: messy delivered-but-not-received dispute with missing POD.
SHP-1003: ambiguous missing promised delivery and unknown customer tier.
SHP-1002 HITL: customer update is attempted, interrupted, approved, then mock-sent.
```

Bad outputs found and fixed:

```text
1. The supervisor invented shipment details before load_shipment_record existed.
2. Some subagents were called with empty request objects.
3. Final summary used unsafe financial authorization wording: "pre-authorized".
```

Fixes:

```text
1. Added load_shipment_record and instructed supervisor to call it first.
2. Added request validation and prompt rules for non-empty subagent requests.
3. Strengthened financial-action wording rules in supervisor and resolution planner prompts.
```

## Part 3: Meta Question

The most tedious repetitive thing I did in the last month was repeatedly testing agent runs by hand: run a prompt, inspect tool calls, compare the output against mock data, write failure notes, adjust prompts or tools, then retest. I would agentify that by building a trace-review assistant that reads a LangSmith run, checks whether required tools fired in the right order, compares outputs against expected behavior, and drafts a failure note automatically. The human would still decide whether the failure is real and what fix to accept, but the repetitive inspection and note drafting could be automated.

## Lessons From The Prototype

The early prototype could produce convincing summaries, but it also invented shipment facts when context was missing. That made the output look polished while being operationally dangerous. The first major improvement was forcing the supervisor to load a source-of-truth shipment record before delegating.

The next failure was orchestration quality. Some tool calls were made with empty arguments. That showed that a working final answer is not enough; the tool trace matters. I fixed that by adding explicit request validation and retesting the messy case.

The final important lesson was human boundaries. The agent correctly paused before sending a customer update, but later used unsafe wording around financial remedies. That made it clear that HITL is not only about tool execution. It is also about language discipline in final summaries. Financial actions must be described as pending human authorization, not as approved or pre-authorized.

This project taught me that a useful agent is not a chatbot with many tools. A useful agent is a controlled workflow that can gather evidence, make bounded recommendations, preserve uncertainty, log its reasoning, and hand off risky decisions to humans.

## Evidence

See:

```text
README.md
manual_workflow.md
test_cases.md
evidence_log.md
failure_notes.md
what_stays_human.md
ai_usage.md
outputs/
```

## Number Source Labels

```text
$48,000 shipment value: observed in mock_data/shipments.json.
$5,000 SLA penalty: observed in mock_data/shipments.json.
$18,000 shipment value: observed in mock_data/shipments.json.
$0 SLA penalty: observed in mock_data/shipments.json.
3 delivery issues in 30 days: assumed mock customer-risk scenario used for testing.
7:06 demo length: observed final video runtime.
```

## What Breaks It

Likely failure modes:

```text
missing shipment ID
shipment record not found
missing promised delivery or customer tier
contradictory carrier and customer evidence
empty subagent tool requests
model inventing missing details
unsafe language around financial remedies
approval required but human does not resume the interrupt
```

Mitigations are documented in:

```text
failure_notes.md
what_stays_human.md
test_cases.md
```
