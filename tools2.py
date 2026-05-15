from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

from langchain.tools import tool


BASE_DIR = Path(__file__).resolve().parent
MOCK_DATA_DIR = BASE_DIR / "mock_data"
RESULTS_DIR = BASE_DIR / "outputs"


def _json(data: dict | list) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def _load_json(filename: str) -> list[dict]:
    path = MOCK_DATA_DIR / filename
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None



@tool
def mock_send_customer_update(
    shipment_id: str,
    customer_name: str,
    message: str,
) -> str:
    """Mock-send a customer update after human approval."""

    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / "approved_customer_updates.json"

    updates = []
    if path.exists():
        updates = json.loads(path.read_text(encoding="utf-8"))

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "shipment_id": shipment_id,
        "customer_name": customer_name,
        "message": message,
        "sent": True,
        "send_type": "mock_customer_update",
    }

    updates.append(record)
    path.write_text(json.dumps(updates, indent=2, sort_keys=True), encoding="utf-8")

    return _json({
        "sent": True,
        "path": str(path),
        "record": record,
    })


@tool
def load_shipment_record(shipment_id: str) -> str:
    """Load the full shipment record from mock shipment data by shipment ID."""
    shipments = _load_json("shipments.json")
    shipment = next((item for item in shipments if item.get("shipment_id") == shipment_id), None)
    if not shipment:
        return _json({
            "shipment_id": shipment_id,
            "found": False,
            "error": "Shipment record not found in mock_data/shipments.json.",
            "human_review_required": True,
        })
    return _json({
        "found": True,
        "shipment": shipment,
    })


@tool
def normalize_exception_code(raw_exception_code: str, raw_exception_message: str = "", carrier: str = "") -> str:
    """Normalize messy carrier exception codes into standard internal labels."""
    code = (raw_exception_code or "").strip().upper()
    message = (raw_exception_message or "").lower()
    mapping = {
        "DELAY": "DELAY",
        "DELAY_MECH": "DELAY",
        "LATE": "DELAY",
        "ADDR_ERR": "ADDRESS_ISSUE",
        "BAD_ADDRESS": "ADDRESS_ISSUE",
        "DAMAGED": "DAMAGED_GOODS",
        "DAMAGE": "DAMAGED_GOODS",
        "NO_SCAN": "NO_TRACKING_UPDATE",
        "STALE_TRACKING": "NO_TRACKING_UPDATE",
        "DELIVERED_DISPUTE": "DELIVERY_DISPUTE",
    }
    normalized = mapping.get(code)
    if not normalized:
        if "address" in message:
            normalized = "ADDRESS_ISSUE"
        elif "damage" in message or "damaged" in message:
            normalized = "DAMAGED_GOODS"
        elif "scan" in message or "tracking" in message:
            normalized = "NO_TRACKING_UPDATE"
        elif "delay" in message or "late" in message:
            normalized = "DELAY"
        else:
            normalized = "UNKNOWN"
    return _json({
        "carrier": carrier,
        "raw_exception_code": raw_exception_code,
        "raw_exception_message": raw_exception_message,
        "normalized_code": normalized,
    })


@tool
def classify_exception_type(normalized_code: str, exception_message: str = "") -> str:
    """Classify a normalized exception code into a business exception type."""
    normalized = (normalized_code or "").upper()
    exception_type = {
        "DELAY": "delay",
        "ADDRESS_ISSUE": "address_issue",
        "DAMAGED_GOODS": "damaged_goods",
        "NO_TRACKING_UPDATE": "no_tracking_update",
        "DELIVERY_DISPUTE": "lost_or_missing_shipment",
    }.get(normalized, "unknown")
    confidence = "high" if exception_type != "unknown" else "low"
    return _json({
        "normalized_code": normalized_code,
        "exception_message": exception_message,
        "exception_type": exception_type,
        "confidence": confidence,
        "reason": f"Mapped {normalized_code} to {exception_type}.",
    })


@tool
def calculate_eta_delta(promised_delivery: str, current_eta: str) -> str:
    """Compare promised delivery against current ETA and calculate lateness in hours."""
    promised = _parse_dt(promised_delivery)
    eta = _parse_dt(current_eta)
    if not promised or not eta:
        return _json({
            "promised_delivery": promised_delivery,
            "current_eta": current_eta,
            "delta_hours": None,
            "is_late": None,
            "missing_fields": ["promised_delivery" if not promised else "", "current_eta" if not eta else ""],
        })
    delta_hours = round((eta - promised).total_seconds() / 3600, 2)
    return _json({
        "promised_delivery": promised_delivery,
        "current_eta": current_eta,
        "delta_hours": delta_hours,
        "is_late": delta_hours > 0,
    })


@tool
def check_sla_breach(
    promised_delivery: str,
    current_eta: str,
    service_level: str = "",
    customer_sla_penalty_usd: int = 0,
) -> str:
    """Determine whether a shipment is likely to breach its SLA."""
    delta = json.loads(calculate_eta_delta.invoke({
        "promised_delivery": promised_delivery,
        "current_eta": current_eta,
    }))
    missing_required = delta.get("is_late") is None
    breach_risk = "unknown" if missing_required else ("high" if delta["is_late"] else "low")
    return _json({
        "service_level": service_level,
        "promised_delivery": promised_delivery,
        "current_eta": current_eta,
        "delta_hours": delta.get("delta_hours"),
        "customer_sla_penalty_usd": customer_sla_penalty_usd,
        "breach_risk": breach_risk,
        "human_review_required": missing_required or breach_risk == "high" or customer_sla_penalty_usd > 0,
    })


@tool
def score_shipment_value_risk(
    shipment_value_usd: int,
    commodity: str = "",
    temperature_control_required: bool = False,
    customer_tier: str = "",
    open_customer_complaint: bool = False,
) -> str:
    """Score business risk from value, commodity, temperature control, and customer importance."""
    score = 0
    if shipment_value_usd >= 50000:
        score += 35
    elif shipment_value_usd >= 10000:
        score += 20
    else:
        score += 10
    if customer_tier.lower() in {"enterprise", "strategic", "priority"}:
        score += 25
    if temperature_control_required:
        score += 25
    if any(term in commodity.lower() for term in ["medical", "pharma", "perishable"]):
        score += 15
    if open_customer_complaint:
        score += 15
    return _json({
        "shipment_value_usd": shipment_value_usd,
        "commodity": commodity,
        "temperature_control_required": temperature_control_required,
        "customer_tier": customer_tier,
        "open_customer_complaint": open_customer_complaint,
        "risk_score": min(score, 100),
    })


@tool
def get_tracking_history(shipment_id: str) -> str:
    """Read tracking events for a shipment from mock tracking data."""
    events = [
        event for event in _load_json("tracking_events.json")
        if event.get("shipment_id") == shipment_id
    ]
    latest = max(events, key=lambda item: item.get("event_time", ""), default=None)
    return _json({
        "shipment_id": shipment_id,
        "events": events,
        "latest_event": latest,
    })


@tool
def detect_stale_tracking(last_tracking_time: str, current_time: str = "", stale_threshold_hours: int = 24) -> str:
    """Check whether tracking has gone stale beyond a threshold."""
    last = _parse_dt(last_tracking_time)
    current = _parse_dt(current_time) or datetime.now(timezone.utc)
    if not last:
        return _json({
            "last_tracking_time": last_tracking_time,
            "current_time": current.isoformat(),
            "stale_threshold_hours": stale_threshold_hours,
            "hours_since_update": None,
            "is_stale": True,
            "reason": "Missing or invalid last_tracking_time.",
        })
    hours_since = round((current - last).total_seconds() / 3600, 2)
    return _json({
        "last_tracking_time": last_tracking_time,
        "current_time": current.isoformat(),
        "stale_threshold_hours": stale_threshold_hours,
        "hours_since_update": hours_since,
        "is_stale": hours_since >= stale_threshold_hours,
    })


@tool
def prepare_carrier_followup(
    shipment_id: str,
    carrier: str,
    exception_type: str,
    missing_information: str = "",
) -> str:
    """Prepare carrier follow-up questions for a human operator."""
    questions = [
        f"What is the confirmed recovery ETA for shipment {shipment_id}?",
        "What caused the exception and is the shipment currently moving?",
        "Is there a recovery option that avoids missing the delivery promise?",
    ]
    if missing_information:
        questions.append(f"Please confirm missing information: {missing_information}.")
    return _json({
        "shipment_id": shipment_id,
        "carrier": carrier,
        "exception_type": exception_type,
        "questions": questions,
        "send_automatically": False,
    })


@tool
def lookup_customer_tier(customer_name: str) -> str:
    """Look up customer tier and account owner from mock customer data."""
    customers = _load_json("customers.json")
    customer = next((item for item in customers if item.get("customer_name") == customer_name), None)
    return _json(customer or {
        "customer_name": customer_name,
        "customer_tier": "unknown",
        "account_owner": "unknown",
        "human_review_required": True,
    })


@tool
def check_open_complaints(customer_name: str, shipment_id: str = "") -> str:
    """Check mock customer data for open complaints."""
    customer = json.loads(lookup_customer_tier.invoke({"customer_name": customer_name}))
    complaints = customer.get("open_complaints", [])
    return _json({
        "customer_name": customer_name,
        "shipment_id": shipment_id,
        "open_complaints": complaints,
        "has_open_complaint": bool(complaints),
    })


@tool
def check_sla_penalty(customer_name: str, service_level: str, promised_delivery: str) -> str:
    """Check whether a customer has SLA penalty exposure for a service level."""
    customer = json.loads(lookup_customer_tier.invoke({"customer_name": customer_name}))
    rules = _load_json("sla_rules.json")
    rule = next(
        (
            item for item in rules
            if item.get("customer_name") == customer_name and item.get("service_level") == service_level
        ),
        None,
    )
    return _json({
        "customer_name": customer_name,
        "customer_tier": customer.get("customer_tier", "unknown"),
        "service_level": service_level,
        "promised_delivery": promised_delivery,
        "penalty_amount": (rule or {}).get("penalty_amount_usd", 0),
        "penalty_condition": (rule or {}).get("penalty_condition", "none"),
    })


@tool
def choose_resolution_route(
    exception_type: str,
    severity: str,
    customer_tier: str = "",
    sla_breach_risk: str = "",
    damaged: bool = False,
    stale_tracking: bool = False,
) -> str:
    """Choose the operational route for a shipment exception."""
    routes = []
    human_review_required = False
    if exception_type == "address_issue":
        routes.append("address_correction_needed")
    if exception_type == "damaged_goods" or damaged:
        routes.append("damage_claim_review")
        human_review_required = True
    if exception_type in {"no_tracking_update", "lost_or_missing_shipment"} or stale_tracking:
        routes.append("lost_shipment_investigation")
        human_review_required = True
    if sla_breach_risk == "high":
        routes.append("customer_notice")
        routes.append("carrier_followup")
    if customer_tier.lower() in {"enterprise", "strategic", "priority"} or severity in {"high", "critical"}:
        human_review_required = True
    if not routes:
        routes.append("monitor_only" if severity == "low" else "carrier_followup")
    if human_review_required:
        routes.append("human_escalation")
    return _json({
        "exception_type": exception_type,
        "severity": severity,
        "customer_tier": customer_tier,
        "sla_breach_risk": sla_breach_risk,
        "routes": sorted(set(routes)),
        "primary_route": routes[0],
        "human_review_required": human_review_required,
    })


@tool
def recommend_next_action(route: str, shipment_id: str, human_review_required: bool = True) -> str:
    """Produce the next practical operator action from a chosen route."""
    actions = {
        "monitor_only": "Monitor the next carrier scan before contacting the customer.",
        "carrier_followup": "Ask the carrier for a confirmed recovery ETA and cause of exception.",
        "customer_notice": "Prepare a customer update with confirmed facts and no unsupported promises.",
        "address_correction_needed": "Request corrected delivery address from customer or account owner.",
        "damage_claim_review": "Escalate to operations to inspect damage evidence and claim eligibility.",
        "lost_shipment_investigation": "Open investigation for missing POD or stale tracking.",
        "human_escalation": "Route to a human operator before customer-facing action.",
    }
    return _json({
        "shipment_id": shipment_id,
        "route": route,
        "action": actions.get(route, "Review exception and decide next action."),
        "urgency": "high" if human_review_required else "normal",
        "human_review_required": human_review_required,
    })


@tool
def draft_customer_update(
    customer_name: str,
    shipment_id: str,
    confirmed_facts: str,
    next_step: str,
    revised_eta: str = "",
) -> str:
    """Draft a customer-safe update without sending it."""
    eta_sentence = f" The current revised ETA is {revised_eta}." if revised_eta else ""
    draft = (
        f"Hi {customer_name}, we are tracking an exception on shipment {shipment_id}. "
        f"Confirmed facts: {confirmed_facts}.{eta_sentence} "
        f"Next step: {next_step}. We will share updates once the carrier confirms recovery details."
    )
    return _json({
        "shipment_id": shipment_id,
        "customer_name": customer_name,
        "draft": draft,
        "send_automatically": False,
        "review_required": True,
    })


@tool
def draft_internal_note(
    shipment_id: str,
    severity: str,
    route: str,
    evidence: str,
    recommended_action: str,
    unresolved_questions: str = "",
) -> str:
    """Draft an internal operations note for the triage result."""
    return _json({
        "shipment_id": shipment_id,
        "severity": severity,
        "route": route,
        "note": (
            f"Shipment {shipment_id} triaged as {severity}. Route: {route}. "
            f"Evidence: {evidence}. Recommended action: {recommended_action}. "
            f"Unresolved questions: {unresolved_questions or 'none'}."
        ),
    })


@tool
def write_evidence_log(
    shipment_id: str,
    route: str,
    severity: str,
    tool_outputs_summary: str,
    assumptions: str = "",
) -> str:
    """Append a run summary to the evidence log for auditability."""
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / "evidence_log.jsonl"
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "shipment_id": shipment_id,
        "route": route,
        "severity": severity,
        "tool_outputs_summary": tool_outputs_summary,
        "assumptions": assumptions,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return _json({
        "saved": True,
        "path": str(path),
        "record": record,
    })


@tool
def save_triage_result(
    shipment_id: str,
    exception_type: str,
    severity: str,
    route: str,
    human_review_required: bool,
    evidence: str,
    drafts: str = "",
) -> str:
    """Save the final structured triage result to mock storage."""
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / "triage_results.json"
    results = []
    if path.exists():
        results = json.loads(path.read_text(encoding="utf-8"))
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "shipment_id": shipment_id,
        "exception_type": exception_type,
        "severity": severity,
        "route": route,
        "human_review_required": human_review_required,
        "evidence": evidence,
        "drafts": drafts,
    }
    results.append(record)
    path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    return _json({
        "saved": True,
        "path": str(path),
        "record": record,
    })
    
    
    
