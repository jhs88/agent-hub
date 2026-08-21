# Issue tracker

Hermes Kanban board **`agent-hub`** is the primary project-management surface. The board is configured locally to use the checkout as its default work directory; repository documentation does not assume a maintainer-specific absolute path.

Useful discovery commands:

```bash
hermes kanban --board agent-hub stats
hermes kanban --board agent-hub list --json
hermes profile list
```

Before assigning a card, discover the profiles available on the current installation and route by capability. Pi or another build helper may draft work, but the orchestrator must inspect artifacts and run acceptance checks before completion.

Local `.scratch/` content is optional disposable planning material linked from a card; it is not the issue tracker and is ignored by Git.

GitHub Issues and external PRs enter the workflow only when the user explicitly requests them. Commit, push, PR, merge, release, and package publication remain separate human approval gates. Agents do not perform those actions automatically.

Do not create a runnable card merely to narrate work already being performed by an interactive operator.
