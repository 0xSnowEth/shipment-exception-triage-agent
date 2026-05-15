import os
import json
from typing import Any
from dotenv import load_dotenv
from langchain_aws import ChatBedrock

try:
    from langchain_aws.agents import create_agent
except ImportError:
    from langchain.agents import create_agent

from langchain.tools import tool
from langgraph.types import interrupt

from tools2 import (
    calculate_eta_delta,
    check_open_complaints,
    check_sla_breach,
    check_sla_penalty,
    choose_resolution_route,
    classify_exception_type,
    detect_stale_tracking,
    draft_customer_update,
    draft_internal_note,
    get_tracking_history,
    load_shipment_record,
    lookup_customer_tier,
    normalize_exception_code,
    prepare_carrier_followup,
    recommend_next_action,
    save_triage_result,
    score_shipment_value_risk,
    write_evidence_log,
    mock_send_customer_update as _mock_send_customer_update,
)



load_dotenv()
os.environ["AWS_BEARER_TOKEN_BEDROCK"] = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "")


llm = ChatBedrock(
    model_id="global.anthropic.claude-opus-4-6-v1",
    region_name="us-east-1",
)


def _last_text(result: dict) -> str:
    message = result["messages"][-1]
    return getattr(message, "text", None) or getattr(message, "content", str(message))


def _require_request(agent_name: str, request: str) -> str | None:
    if request and request.strip():
        return None
    return (
        f"{agent_name} was called without a non-empty request. "
        "Retry with the loaded shipment facts and the exact task this subagent must perform."
    )


def _normalize_human_decision(value: Any) -> tuple[str, str, dict[str, Any]]:
    """Accept simple Studio resume values and structured HITL decision objects."""
    if isinstance(value, str):
        return value.strip().lower(), "", {}

    if isinstance(value, list) and value:
        return _normalize_human_decision(value[0])

    if not isinstance(value, dict):
        return "invalid", f"Unsupported resume value: {value!r}", {}

    if "decisions" in value:
        decisions = value.get("decisions") or []
        return _normalize_human_decision(decisions[0] if decisions else {})

    decision = str(value.get("decision") or value.get("type") or "").strip().lower()
    message = str(value.get("message") or value.get("reason") or "")

    edited_action = value.get("edited_action") or {}
    edited_args = value.get("args") or edited_action.get("args") or {}

    return decision, message, edited_args if isinstance(edited_args, dict) else {}


@tool
def mock_send_customer_update(
    shipment_id: str,
    customer_name: str,
    message: str,
) -> str:
    """Pause for human approval before mock-sending a customer update."""
    decision_value = interrupt({
        "action": "mock_send_customer_update",
        "description": "Human approval required before customer-facing action.",
        "args": {
            "shipment_id": shipment_id,
            "customer_name": customer_name,
            "message": message,
        },
        "allowed_decisions": ["approve", "edit", "reject"],
        "resume_examples": [
            "\"approve\"",
            {"decision": "approve"},
            {"decisions": [{"type": "approve"}]},
        ],
    })

    decision, reason, edited_args = _normalize_human_decision(decision_value)

    if decision == "reject":
        return json.dumps({
            "sent": False,
            "approved": False,
            "decision": "reject",
            "reason": reason or "Human rejected the customer update.",
        }, indent=2, sort_keys=True)

    if decision == "edit":
        shipment_id = str(edited_args.get("shipment_id", shipment_id))
        customer_name = str(edited_args.get("customer_name", customer_name))
        message = str(edited_args.get("message", message))
        decision = "approve"

    if decision != "approve":
        return json.dumps({
            "sent": False,
            "approved": False,
            "decision": decision or "missing",
            "error": "Expected approval resume value: approve, reject, edit, or a decision object.",
        }, indent=2, sort_keys=True)

    return _mock_send_customer_update.invoke({
        "shipment_id": shipment_id,
        "customer_name": customer_name,
        "message": message,
    })


EXCEPTION_CLASSIFIER_PROMPT = (
    "You are the exception classifier agent for logistics shipment triage. "
    "Use your tools to normalize carrier exception codes and classify the business exception type. "
    "Return the exception type, confidence, and reason. Do not plan resolution."
)

IMPACT_ASSESSMENT_PROMPT = (
    "You are the impact assessment agent. "
    "Use tools to calculate ETA delta, SLA breach risk, and shipment value risk. "
    "Return severity evidence using only provided data. If required fields are missing, say so."
)

CARRIER_STATUS_PROMPT = (
    "You are the carrier status agent. "
    "Use tools to inspect tracking history, stale tracking risk, and carrier follow-up questions. "
    "Return only carrier/tracking facts and unresolved questions."
)

CUSTOMER_RISK_PROMPT = (
    "You are the customer risk agent. "
    "Use tools to check customer tier, open complaints, and SLA penalty exposure. "
    "Return customer risk facts and whether proactive human review is needed."
)

RESOLUTION_PLANNER_PROMPT = (
    "You are the resolution planner agent. "
    "Never say refunds, credits, replacements, chargebacks, claims, reships, penalties, or financial contingencies are approved, pre-authorized, initiated, granted, or triggered. These actions may only be described as prepared for human review, recommended for human evaluation, or pending human authorization."
    "Use tools to choose the route and next action from exception type, impact, carrier status, and customer risk. "
    "Never send customer messages or approve costly actions. Flag human_review_required for risky cases."
)

COMMUNICATION_DRAFT_PROMPT = (
    "You are the communication draft agent. "
    "Use tools to draft customer-safe updates and internal notes. "
    "Do not overpromise. Do not claim carrier confirmation unless provided. Do not send anything."
)

EVIDENCE_REPORT_PROMPT = (
    "You are the evidence report agent. "
    "Use tools to save the final triage result and write an evidence log. "
    "Summarize exactly what was saved and which assumptions remain."
)

SUPERVISOR_PROMPT = (
    "You are the shipment exception supervisor for a logistics operations workflow. "
    "Your job is to coordinate specialized subagents to triage shipment exceptions. "
    "Always call load_shipment_record first when the user provides a shipment ID. "
    "Use the loaded shipment JSON as the source of truth and pass the actual fields to subagents. "
    "Do not invent customer names, shipment values, service levels, promised delivery times, SLA penalties, or ETAs. "
    "Every subagent tool requires a non-empty request argument. Never call a subagent tool with an empty object. "
    "When calling a subagent, include the shipment ID, relevant loaded shipment fields, and the specific task to perform. "
    "For each shipment exception, delegate to the relevant agents: "
    "exception_classifier_agent for exception type, impact_assessment_agent for ETA/SLA/value risk, "
    "carrier_status_agent for tracking and carrier follow-up, customer_risk_agent for customer/SLA risk, "
    "resolution_planner_agent for route and next action, communication_draft_agent for drafts, "
    "and evidence_report_agent for saving results. "
    "Never say refunds, credits, replacements, chargebacks, claims, reships, penalties, or financial contingencies are approved, pre-authorized, initiated, granted, or triggered. These actions may only be described as prepared for human review, recommended for human evaluation, or pending human authorization."
    "If a customer-facing update should be sent, first create the draft with communication_draft_agent. Then call mock_send_customer_update with the final approved draft. This tool requires human approval and must not be bypassed."
    "Prefer parallel delegation when classification, impact, carrier status, and customer risk can be assessed independently. "
    "Never send customer messages automatically. High-risk, ambiguous, damaged, lost, stale-tracking, SLA-penalty, "
    "or enterprise-customer cases require human review. Final response must include route, severity, evidence, "
    "human_review_required, and next action."
)


exception_classifier = create_agent(
    model=llm,
    tools=[normalize_exception_code, classify_exception_type],
    system_prompt=EXCEPTION_CLASSIFIER_PROMPT,
)

impact_assessment = create_agent(
    model=llm,
    tools=[calculate_eta_delta, check_sla_breach, score_shipment_value_risk],
    system_prompt=IMPACT_ASSESSMENT_PROMPT,
)

carrier_status = create_agent(
    model=llm,
    tools=[get_tracking_history, detect_stale_tracking, prepare_carrier_followup],
    system_prompt=CARRIER_STATUS_PROMPT,
)

customer_risk = create_agent(
    model=llm,
    tools=[lookup_customer_tier, check_open_complaints, check_sla_penalty],
    system_prompt=CUSTOMER_RISK_PROMPT,
)

resolution_planner = create_agent(
    model=llm,
    tools=[choose_resolution_route, recommend_next_action],
    system_prompt=RESOLUTION_PLANNER_PROMPT,
)

communication_draft = create_agent(
    model=llm,
    tools=[draft_customer_update, draft_internal_note],
    system_prompt=COMMUNICATION_DRAFT_PROMPT,
)

evidence_report = create_agent(
    model=llm,
    tools=[write_evidence_log, save_triage_result],
    system_prompt=EVIDENCE_REPORT_PROMPT,
)

#This agent basically calls 2 tools, in which the first one would be:
"1. Normalize exception code: In which the sole purpose is to recieve any messt carrier or exception messages and actually put the context into their own labels which it would then call the next following tool:"
"2. Classify exception type: Which the sole purpose is to recieve the Normalized clear labels of the exception code and classifies them based off of their status in sverity ('high', 'medium', 'low')"
@tool
def exception_classifier_agent(request: str) -> str:
    """Classify raw carrier exception details into a normalized logistics exception type."""
    error = _require_request("exception_classifier_agent", request)
    if error:
        return error
    result = exception_classifier.invoke({"messages": [{"role": "user", "content": request}]})
    return _last_text(result)


@tool
def impact_assessment_agent(request: str) -> str:
    """Assess ETA delay, SLA breach risk, shipment value risk, and likely severity."""
    error = _require_request("impact_assessment_agent", request)
    if error:
        return error
    result = impact_assessment.invoke({"messages": [{"role": "user", "content": request}]})
    return _last_text(result)


@tool
def carrier_status_agent(request: str) -> str:
    """Inspect tracking history, stale-tracking risk, and carrier follow-up needs."""
    error = _require_request("carrier_status_agent", request)
    if error:
        return error
    result = carrier_status.invoke({"messages": [{"role": "user", "content": request}]})
    return _last_text(result)


@tool
def customer_risk_agent(request: str) -> str:
    """Check customer tier, open complaints, SLA penalties, and notification risk."""
    error = _require_request("customer_risk_agent", request)
    if error:
        return error
    result = customer_risk.invoke({"messages": [{"role": "user", "content": request}]})
    return _last_text(result)


@tool
def resolution_planner_agent(request: str) -> str:
    """Choose route and next action from exception, impact, carrier, and customer risk evidence."""
    error = _require_request("resolution_planner_agent", request)
    if error:
        return error
    result = resolution_planner.invoke({"messages": [{"role": "user", "content": request}]})
    return _last_text(result)


@tool
def communication_draft_agent(request: str) -> str:
    """Draft customer-safe updates and internal notes without sending anything."""
    error = _require_request("communication_draft_agent", request)
    if error:
        return error
    result = communication_draft.invoke({"messages": [{"role": "user", "content": request}]})
    return _last_text(result)


@tool
def evidence_report_agent(request: str) -> str:
    """Save final triage result and evidence log for auditability."""
    error = _require_request("evidence_report_agent", request)
    if error:
        return error
    result = evidence_report.invoke({"messages": [{"role": "user", "content": request}]})
    return _last_text(result)





shipment_exception_supervisor = create_agent(
    model=llm,
    tools=[
        load_shipment_record,
        exception_classifier_agent,
        impact_assessment_agent,
        carrier_status_agent,
        customer_risk_agent,
        resolution_planner_agent,
        communication_draft_agent,
        evidence_report_agent,
        mock_send_customer_update,
    ],
    system_prompt=SUPERVISOR_PROMPT,
)
