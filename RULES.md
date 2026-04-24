# Backend Rules

## Logging Rule

- When changing backend request flow, add structured logs for request start, success, and failure paths.
- Use `app.utils.logger.trace_logic(...)` for logic-level traces so the same event is written to the logger and printed to stdout.
- Keep logs compact and useful: include ids, route intent, pagination, status, and error text, but never print secrets, tokens, or raw passwords.
- Prefer one trace at route entry and one trace after the main state change completes.
- For new database or external-service integrations, log whether config is present and whether connectivity succeeded or failed.

## Debug Rule

- `DEBUG_TRACE_ENABLED=true` is allowed in development so backend logic prints JSON traces to container logs.
- If logs become too noisy, turn off `DEBUG_TRACE_ENABLED` instead of deleting trace calls.
