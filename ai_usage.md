# AI Usage Disclosure

## Tools Used

```text
Codex: used as an AI pair-programming assistant for review, debugging support, and documentation cleanup.
LangGraph / LangChain documentation: used to verify agent, tool, subagent, Studio, and HITL implementation patterns.
LangGraph Studio: used to run the agent and inspect visible tool calls.
LangSmith: used to inspect execution traces and verify tool-call order.
```

## What AI Helped With

```text
reviewing the repo structure
suggesting implementation patterns for LangGraph/LangChain
drafting first-pass documentation sections
debugging failed graph imports and HITL resume behavior
spotting risks in tool-call traces and final outputs
```

## What I Owned

```text
chose the logistics shipment exception triage workflow
approved the manual workflow and business boundaries
ran the LangGraph Studio tests
inspected the tool calls and traces manually
identified hallucinated shipment facts
identified empty subagent requests
identified unsafe financial authorization wording
decided what should stay human-owned
approved the HITL customer update test
judged whether each test passed or failed
prepared the final demo and submission judgment
```

## What I Manually Verified

```text
load_shipment_record runs before subagent delegation
SHP-1001 uses mock shipment facts instead of invented facts
SHP-1002 handles delivered-but-not-received as a delivery dispute / lost shipment investigation
SHP-1003 preserves missing promised delivery and unknown customer tier
mock_send_customer_update pauses before customer-facing action
approved customer updates are written only after human approval
financial remedies are described as pending human authorization, not approved
```

## Human Boundary

AI was used to accelerate implementation and review, but final acceptance depended on manual testing in LangGraph Studio, visible tool-call inspection, output comparison against mock data, failure notes, and retests.
