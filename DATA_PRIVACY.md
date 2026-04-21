# Data Privacy & PII Handling

This project handles citizen-submitted messages. The following guidance and protections are implemented or recommended:

- PII Redaction: AI outputs are sanitized to avoid returning personal names, locations or contact details. Use `redaction` utility before persisting or returning texts.
- Minimization: Stored reports are minimal structured records (issue, emotion, urgency, summary, message) and should avoid storing sensitive contact details.
- Access Controls: In production, restrict `/reports` and admin endpoints to authenticated admin users only.
- Retention: Implement retention or archival for `reports.json`; consider rotating or anonymizing older records.
- Audit: Log access to sensitive endpoints and preserve telemetry for monitoring access patterns.
