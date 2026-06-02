## Use agent as tool
The task is mostly conversational and dynamic.
One coordinator can decide “which specialist to call” on the fly.
Steps are short, usually 1–3 tool/agent calls.
You do not need strict execution order, checkpoints, or retries.
Best-effort behavior is acceptable.

### Good fit examples:
“Answer this customer question; use billing specialist only if needed.”
“Summarize this doc and optionally ask the math agent for one calculation.”

## Use workflow
You need deterministic stages (ingest → validate → enrich → approve → publish).
You need branching/parallelism with explicit joins.
You need durability, resumability, retries, timeouts, compensation.
You need auditability/SLA/compliance and predictable outcomes.
You need human-in-the-loop gates.

### Good fit examples:
Ticket triage pipeline with policy checks and approval.
Multi-source ETL/report generation with retries and failure handling.
Order/refund process where each step must be recorded and reversible.

## Rule of thumb
If you can describe it as “let the coordinator reason and delegate,” use agent-as-tool.
If you can describe it as a flowchart with required boxes/arrows, use workflow.

## Hybrid (common in production)
Workflow orchestrates the business process.
Inside a workflow step, an agent uses agent-as-tool for flexible reasoning/subtasks.
This gives you reliability at the process layer and intelligence at the task layer.