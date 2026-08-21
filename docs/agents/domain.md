# Domain documentation

Agent Hub is a single-context repository.

Before exploring or changing code:

1. Read `CONTEXT.md` for canonical vocabulary and stable invariants.
2. Read ADRs under `docs/adr/` that touch the proposed change.
3. Read `DESIGN.md` for the current module/interface shape and migration boundary.

Use glossary terms in specs, cards, tests, and code. If a needed concept is absent, treat that as a domain-modeling question rather than silently introducing a synonym.

If a proposal contradicts an accepted ADR, name the conflict and create a superseding decision instead of silently overriding the record.
