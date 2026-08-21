# Architecture decision records

ADRs capture durable Agent Hub decisions that future implementation work must preserve or explicitly supersede.

- Use sequential names such as `0003-short-title.md`.
- Record status, context, decision, and consequences.
- Accepted ADRs remain historical evidence; supersede rather than rewrite their decision.
- Keep implementation detail in code and `DESIGN.md`; use ADRs for choices whose alternatives matter.

Current decisions:

- [ADR-0001: Session helper with thin desktop adapters](0001-session-helper-and-thin-adapters.md)
- [ADR-0002: Allow-listed aggregate snapshot](0002-allow-listed-aggregate-snapshot.md)
