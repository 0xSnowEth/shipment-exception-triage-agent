# Manual Workflow

## Logistics Shipment Exception Triage

This workflow is normally handled by a dispatcher, logistics coordinator, account owner, or operations analyst when a shipment exception appears in a TMS or carrier portal.

Manual process:

```text
1. A shipment exception appears in the TMS, carrier portal, support inbox, or customer escalation channel.
2. The operator opens the shipment record and reviews shipment ID, order ID, carrier, origin, destination, service level, commodity, value, customer, and customer tier.
3. The operator compares promised delivery against the current ETA.
4. The operator checks whether the exception creates SLA exposure or customer escalation risk.
5. The operator inspects the latest carrier scan and tracking history.
6. The operator checks whether tracking is stale, contradictory, sparse, or missing proof of delivery.
7. The operator classifies the exception: delay, address issue, damaged goods, no tracking update, delivery dispute, lost/missing shipment, or unknown.
8. The operator estimates severity based on ETA impact, shipment value, commodity risk, customer tier, complaint history, and missing evidence.
9. The operator chooses the operational route: monitor, contact carrier, notify customer, correct address, investigate loss, review damage, or escalate to a human.
10. The operator drafts a customer-safe update using only confirmed facts.
11. The operator saves evidence so another reviewer can understand why the route was chosen.
12. The operator routes the case to a human before customer-facing, financial, claim, or irreversible action.
```

Why this is a good agent workflow:

- It is repetitive and evidence-heavy.
- It requires pulling context from multiple sources.
- It has clear decision routes.
- It benefits from fast first-pass triage.
- It still needs human approval for customer trust, financial exposure, and operational liability.
