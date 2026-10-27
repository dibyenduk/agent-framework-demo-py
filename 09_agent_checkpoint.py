"""Stop at human approval, then resume the saved draft in a later process.

Run with ``python 09_agent_checkpoint.py``. At the approval prompt, type
``pause`` (or ``exit``) to stop, ``approve`` to finish, or revision guidance to
request another draft. Restart and select the saved run to continue.

Each new run has its own directory under ``tmp/checkpoints_hitl``. Checkpoints
are immutable history snapshots, not a queue: only the latest snapshot of each
run determines whether it still needs approval. Completed history is retained
but is not offered for resume. Legacy checkpoints directly in the root are
treated as one older run, using only its latest snapshot.
"""

import asyncio
import sys
from agent_framework.foundry import FoundryChatClient
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from agent_framework import (
    Agent,
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    Executor,
    FileCheckpointStorage,
    Message,
    Workflow,
    WorkflowBuilder,
    WorkflowCheckpoint,
    WorkflowContext,
    handler,
    response_handler,
)
from utils.config import get_foundry_client


if sys.version_info >= (3, 12):
    from typing import override  # type: ignore # pragma: no cover
else:
    from typing_extensions import override  # type: ignore[import] # pragma: no cover

TEMP_DIR = Path(__file__).resolve().parent / "tmp" / "checkpoints_hitl"
WORKFLOW_NAME = "coffee_grinder_workflow"


class BriefPreparer(Executor):
    """Normalises the user brief and sends a single AgentExecutorRequest."""

    # The first executor in the workflow. By keeping it tiny we make it easier
    # to reason about the state that will later be captured in the checkpoint.
    # It is responsible for tidying the human-provided brief and kicking off the
    # agent run with a deterministic prompt structure.

    def __init__(self, id: str, agent_id: str) -> None:
        super().__init__(id=id)
        self._agent_id = agent_id

    @handler
    async def prepare(self, brief: str, ctx: WorkflowContext[AgentExecutorRequest, str]) -> None:
        # Collapse errant whitespace so the prompt is stable between runs.
        normalized = " ".join(brief.split()).strip()
        if not normalized.endswith("."):
            normalized += "."
        # Persist the cleaned brief in workflow state so downstream executors and
        # future checkpoints can recover the original intent.
        ctx.set_state("brief", normalized)
        prompt = (
            "You are drafting product release notes. Summarise the brief below in two sentences. "
            "Keep it positive and end with a call to action.\n\n"
            f"BRIEF: {normalized}"
        )
        # Hand the prompt to the writer agent. We always route through the
        # workflow context so the runtime can capture messages for checkpointing.
        await ctx.send_message(
            AgentExecutorRequest(messages=[Message("user", contents=[prompt])], should_respond=True),
            target_id=self._agent_id,
        )


@dataclass
class HumanApprovalRequest:
    """Request sent to the human reviewer."""

    # The dataclass is allowlisted by create_storage for checkpoint restoration.
    prompt: str = ""
    draft: str = ""
    iteration: int = 0


class ReviewGateway(Executor):
    """Routes agent drafts to humans and optionally back for revisions."""

    def __init__(self, id: str, writer_id: str) -> None:
        super().__init__(id=id)
        self._writer_id = writer_id
        self._iteration = 0

    @handler
    async def on_agent_response(self, response: AgentExecutorResponse, ctx: WorkflowContext) -> None:
        # Capture the agent output so we can surface it to the reviewer and persist iterations.
        self._iteration += 1

        request_data = HumanApprovalRequest(
            prompt="Review the draft. Reply 'approve' or provide edit instructions.",
            draft=response.agent_response.text,
            iteration=self._iteration,
        )
        await ctx.request_info(
            request_data=request_data,
            response_type=str,
        )

    @response_handler
    async def on_human_feedback(
        self,
        original_request: HumanApprovalRequest,
        feedback: str,
        ctx: WorkflowContext[AgentExecutorRequest | str, str],
    ) -> None:
        # The `original_request` is the request we sent earlier that is now being answered.
        reply = feedback.strip()
        if not reply:
            raise ValueError("Approval requires 'approve' or non-empty revision guidance.")

        if reply.lower() == "approve":
            # Workflow is completed when the human approves.
            await ctx.yield_output(original_request.draft)
            return

        # Any other response loops us back to the writer with fresh guidance.
        prompt = (
            "Revise the launch note. Respond with the new copy only.\n\n"
            f"Previous draft:\n{original_request.draft}\n\n"
            f"Human guidance: {reply}"
        )
        await ctx.send_message(
            AgentExecutorRequest(messages=[Message("user", contents=[prompt])], should_respond=True),
            target_id=self._writer_id,
        )

    @override
    async def on_checkpoint_save(self) -> dict[str, Any]:
        return {"iteration": self._iteration}

    @override
    async def on_checkpoint_restore(self, state: dict[str, Any]) -> None:
        self._iteration = state.get("iteration", 0)


def read_input(prompt: str) -> str | None:
    """Treat an interrupted CLI prompt as a pause, not an approval."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nInput interrupted. Existing checkpoints are preserved.")
        return None


def prompt_for_responses(requests: dict[str, HumanApprovalRequest]) -> dict[str, str] | None:
    """Interactive CLI prompt for any live RequestInfo requests."""

    responses: dict[str, str] = {}
    for request_id, request in requests.items():
        print("\n=== Human approval needed ===")
        print(f"request_id: {request_id}")
        print(f"Iteration: {request.iteration}")
        print(request.prompt)
        print("Draft: \n---\n" + request.draft + "\n---")
        while True:
            response = read_input("Type 'approve', revision guidance, or 'pause'/'exit' to stop: ")
            if response is None or response.lower() in {"pause", "exit"}:
                return None
            if response:
                responses[request_id] = response
                break
            print("Empty input does not approve the draft. Enter 'approve', guidance, or 'pause'.")

    return responses


async def run_interactive_session(
    workflow: Workflow,
    storage: FileCheckpointStorage,
    initial_message: str | None = None,
    checkpoint_id: str | None = None,
) -> str | None:
    """Run the workflow until it either finishes or pauses for human input."""

    requests: dict[str, HumanApprovalRequest] = {}
    responses: dict[str, str] | None = None
    completed_output: str | None = None

    while True:
        if responses is not None:
            event_stream = workflow.run(stream=True, responses=responses)
            requests.clear()
            responses = None
        else:
            if initial_message is not None:
                print(f"\nStarting workflow with brief: {initial_message}\n")
                event_stream = workflow.run(message=initial_message, stream=True)
                initial_message = None
            elif checkpoint_id:
                print("\nStarting workflow from checkpoint...\n")
                event_stream = workflow.run(checkpoint_id=checkpoint_id, stream=True)
                checkpoint_id = None
            else:
                raise ValueError("Either initial_message or checkpoint_id must be provided")

        async for event in event_stream:
            if event.type == "output":
                # Only treat string outputs as final; AgentResponseUpdate is intermediate
                if isinstance(event.data, str):
                    completed_output = event.data
            elif event.type == "request_info":
                if isinstance(event.data, HumanApprovalRequest):
                    requests[event.request_id] = event.data
                else:
                    raise ValueError(f"Unexpected request data type: {type(event.data)}")

        if completed_output is not None:
            return completed_output

        if requests:
            checkpoint = await storage.get_latest(workflow_name=WORKFLOW_NAME)
            if checkpoint is None or not checkpoint.pending_request_info_events:
                raise RuntimeError("Human approval was requested but no pending checkpoint was saved.")
            print(f"\nSaved approval checkpoint: {checkpoint.checkpoint_id}")
            print(f"Checkpoint directory: {storage.storage_path}")
            responses = prompt_for_responses(requests)
            if responses is None:
                print("\nPaused safely. Restart this script and select this run to resume the saved draft.")
                return None
            continue

        raise RuntimeError("Workflow stopped without a final draft or pending human approval.")


@dataclass
class PendingRun:
    storage_path: Path
    checkpoint: WorkflowCheckpoint


def create_storage(storage_path: Path) -> FileCheckpointStorage:
    return FileCheckpointStorage(
        storage_path=storage_path,
        allowed_checkpoint_types=[f"{HumanApprovalRequest.__module__}:HumanApprovalRequest"],
    )


async def find_pending_runs(checkpoint_root: Path) -> list[PendingRun]:
    """Only the latest snapshot in each isolated run can be awaiting approval."""
    if not checkpoint_root.exists():
        return []

    run_paths = [checkpoint_root]
    run_paths.extend(
        path for path in checkpoint_root.iterdir() if path.is_dir() and path.name.startswith("run-")
    )
    pending_runs = []
    for storage_path in run_paths:
        latest = await create_storage(storage_path).get_latest(workflow_name=WORKFLOW_NAME)
        if latest is not None and latest.pending_request_info_events:
            pending_runs.append(PendingRun(storage_path, latest))
    return sorted(pending_runs, key=lambda run: datetime.fromisoformat(run.checkpoint.timestamp))


def build_workflow(storage: FileCheckpointStorage) -> Workflow:
    """Build fresh executor instances for either a new run or checkpoint restore."""
    writer_agent = Agent(
        client=get_foundry_client(),
        instructions="Write concise, warm release notes that sound human and helpful.",
        name="writer",
    )
    writer = AgentExecutor(writer_agent)
    review_gateway = ReviewGateway(id="review_gateway", writer_id="writer")
    prepare_brief = BriefPreparer(id="prepare_brief", agent_id="writer")

    return (
        WorkflowBuilder(
            name=WORKFLOW_NAME,
            max_iterations=20,
            start_executor=prepare_brief,
            checkpoint_storage=storage,
            output_from=[review_gateway],
        )
        .add_edge(prepare_brief, writer)
        .add_edge(writer, review_gateway)
        .add_edge(review_gateway, writer)
        .build()
    )


async def main(checkpoint_root: Path = TEMP_DIR) -> None:
    """Choose a pending run or create a separate run without deleting history."""
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    pending_runs = await find_pending_runs(checkpoint_root)
    chosen: PendingRun | None = None
    if pending_runs:
        print(f"\nFound {len(pending_runs)} run(s) awaiting human approval:")
        for index, run in enumerate(pending_runs):
            label = "legacy" if run.storage_path == checkpoint_root else run.storage_path.name
            print(f"  [{index}] {label}: checkpoint={run.checkpoint.checkpoint_id}")
        while True:
            selection = read_input("\nEnter index (Enter = latest), 'new', or 'exit': ")
            if selection is None or selection.lower() == "exit":
                print("Stopped. Existing checkpoints are preserved.")
                return
            if selection.lower() == "new":
                break
            try:
                index = int(selection) if selection else len(pending_runs) - 1
            except ValueError:
                print("Invalid selection. Enter a listed index, 'new', or 'exit'.")
                continue
            if 0 <= index < len(pending_runs):
                chosen = pending_runs[index]
                break
            print("Index out of range. Choose a listed run.")

    brief = (
        "Introduce our limited edition smart coffee grinder. Mention the $249 price, highlight the "
        "sensor that auto-adjusts the grind, and invite customers to pre-order on the website."
    )

    storage_path = chosen.storage_path if chosen else checkpoint_root / f"run-{uuid4()}"
    storage = create_storage(storage_path)
    print(f"\nRun directory: {storage_path}")
    workflow = build_workflow(storage)
    result = await run_interactive_session(
        workflow,
        storage,
        checkpoint_id=chosen.checkpoint.checkpoint_id if chosen else None,
        initial_message=None if chosen else brief,
    )
    if result is not None:
        print(f"\nWorkflow completed. Approved draft:\n{result}")
        print(f"\nCheckpoint history retained in: {storage_path}")
        print("This completed run will not be offered for resume.")


if __name__ == "__main__":
    asyncio.run(main())