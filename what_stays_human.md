# What Stays Human

The agent is allowed to:
- load shipment records
- classify exceptions
- assess ETA/SLA/customer risk
- inspect tracking evidence
- recommend a resolution route
- draft customer-safe messages
- save evidence logs
- prepare carrier follow-up questions

The agent is not allowed to automatically:
- send customer-facing messages
- approve refunds, credits, or replacements
- file carrier claims
- mark a shipment permanently lost
- rebook shipments with extra cost
- promise a delivery time unless carrier-confirmed
- change customer/order records
- close an incident without human review

Human approval is required when:
- shipment value is high
- customer is priority/enterprise
- POD is missing
- SLA penalty exists
- customer tier or promised delivery is unknown
- tracking is stale or contradictory
- the recommended action creates cost, liability, or customer impact
