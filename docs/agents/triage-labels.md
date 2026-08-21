# Triage roles

Matt skills use five canonical triage roles. For this project they map directly to Hermes Kanban state:

| Canonical role | Board representation | Meaning |
|---|---|---|
| `needs-triage` | `triage` | The request needs classification and scope. |
| `needs-info` | `blocked` | Blocked with one precise unanswered question. |
| `ready-for-agent` | `ready` | Acceptance criteria are complete and a valid capability profile is assigned. |
| `ready-for-human` | `blocked` | A named human decision or action is required. |
| `wontfix` | `archived` | Closed with a concise explanation. |

These are development workflow states. They are not Agent Hub runtime concepts and must not appear in the Snapshot schema.
