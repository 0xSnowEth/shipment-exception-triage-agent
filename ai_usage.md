# AI Usage Disclosure

## Tools Used

```text
Codex: repo review, architecture guidance, code scaffolding, documentation drafting, debugging support.
LangChain / LangGraph docs: agent creation, tools, subagents, LangGraph Studio, HITL interrupts, local server.
LangSmith Studio: manual UI testing, visible tool-call inspection, HITL approval testing.
```

## AI Helped With

```text
repo structure
supervisor-subagent architecture
subagent prompt first drafts
tool scaffolds
mock data format
README and submission document structure
test case formatting
debugging failed graph imports
debugging empty tool-call requests
debugging HITL resume behavior
identifying unsafe output wording
```

## Human-Owned Work

```text
choosing logistics shipment exception triage as the workflow
approving the manual workflow
running the LangGraph Studio tests
inspecting tool calls manually
deciding whether outputs passed or failed
detecting hallucinated shipment facts
detecting empty subagent tool calls
detecting unsafe financial authorization wording
approving the HITL customer update test
deciding human approval boundaries
final submission judgment
```

## What Was Manually Verified

```text
load_shipment_record runs before subagent delegation
SHP-1001 uses mock shipment facts instead of invented facts
SHP-1002 handles delivered-but-not-received as a delivery dispute / lost shipment investigation
SHP-1003 preserves missing promised delivery and unknown customer tier
mock_send_customer_update pauses before customer-facing action
approved customer updates are written only after human approval
financial remedies are described as pending human authorization, not approved
```
