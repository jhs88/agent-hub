# ADR-0002: Allow-listed aggregate snapshot

- Status: Accepted
- Date: 2026-08-21

## Context

Collector inputs include transcripts, provider payloads, SQLite rows, and authentication-adjacent state. Passing arbitrary upstream keys to desktop shells would make privacy depend on every provider remaining unchanged.

## Decision

Project all client-visible state into a recursively allow-listed Snapshot. Include provider/model IDs, timestamps, token totals, prompt/session counts, quota windows, Agent availability, and Default Agent state. Strip unknown keys at every nested level.

Snapshot consumers render external labels as plain text. Missing or invalid input is skipped or represented as unknown; it is never replaced with fabricated usage.

## Consequences

- Prompt/response text, credentials, auth headers, account email, and transcript paths cannot appear merely because an upstream schema expands.
- Adding a new field requires an explicit schema and test change.
- Desktop adapters remain provider-agnostic.
- Fixture tests with private sentinels are a release gate.
