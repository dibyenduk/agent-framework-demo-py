import asyncio
from http import client
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

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
    WorkflowContext,
    handler,
    response_handler,
)
from agent_framework.foundry import FoundryChatClient
from utils.config import get_foundry_client


if sys.version_info >= (3, 12):
    from typing import override  # type: ignore # pragma: no cover
else:
    from typing_extensions import override  # type: ignore[import] # pragma: no cover

"""
Sample: Checkpoint + human-in-the-loop quickstart.

This getting-started sample keeps the moving pieces to a minimum:

1. A brief is turned into a consistent prompt for an AI copywriter.
2. The copywriter (an `AgentExecutor`) drafts release notes.
3. A reviewer gateway sends a request for approval for every draft.
4. The workflow records checkpoints between each superstep so you can stop the
   program, restart later, and optionally pre-supply human answers on resume.

Key concepts demonstrated
-------------------------
- Minimal executor pipeline with checkpoint persistence.
- Human-in-the-loop pause/resume with checkpoint restoration.

Typical pause/resume flow
-------------------------
1. Run the workflow until a human approval request is emitted.
2. If the human is offline, exit the program. A checkpoint with
   ``status=awaiting human response`` now exists.
3. Later, restart the script, select that checkpoint, and provide the stored
   human decision when prompted to pre-supply responses.
   Doing so applies the answer immediately on resume, so the system does **not**
   re-emit the same ``.
"""

# Directory used for the sample's temporary checkpoint files. We isolate the
# demo artefacts so that repeated runs do not collide with other samples and so
# the clean-up step at the end of the script can simply delete the directory.
TEMP_DIR = Path(__file__).with_suffix("").parent / "tmp" / "checkpoints_hitl"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


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

    # These fields are intentionally simple because they are serialised into
    # checkpoints. Keeping them primitive types guarantees the new
    # `pending_requests_from_checkpoint` helper can reconstruct them on resume.
    prompt: str = ""
    draft: str = ""
    iteration: int = 0


class ReviewGateway(Executor):
    """Routes agent drafts to humans and optionally back for revisions."""

    def __init__(self, id: str, writer_id: str) -> None:
        super().__init__(id=id)
        self._writer_id = writer_id
        self._iteration = 0
        self._pending_request: HumanApprovalRequest | None = None
        self._pending_request_id: str | None = None

    @handler
    async def on_agent_response(self, response: AgentExecutorResponse, ctx: WorkflowContext) -> None:
        # Capture the agent output so we can surface it to the reviewer and persist iterations.
        self._iteration += 1

        # Create and store the pending request for potential checkpoint restoration
        request_data = HumanApprovalRequest(
            prompt="Review the draft. Reply 'approve' or provide edit instructions.",
            draft=response.agent_response.text,
            iteration=self._iteration,
        )
        self._pending_request = request_data
        
        # Emit a human approval request.
        response_info = await ctx.request_info(
            request_data=request_data,
            response_type=str,
        )
        self._pending_request_id = response_info

    @response_handler
    async def on_human_feedback(
        self,
        original_request: HumanApprovalRequest,
        feedback: str,
        ctx: WorkflowContext[AgentExecutorRequest | str, str],
    ) -> None:
        # The `original_request` is the request we sent earlier that is now being answered.
        reply = feedback.strip()
        # Clear pending request since we're now handling it
        self._pending_request = None
        self._pending_request_id = None

        if len(reply) == 0 or reply.lower() == "approve":
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

    def has_pending_request(self) -> bool:
        """Check if there's a pending human approval request."""
        return self._pending_request is not None

    def get_pending_request(self) -> HumanApprovalRequest | None:
        """Get the pending human approval request."""
        return self._pending_request

    @override
    async def on_checkpoint_save(self) -> dict[str, Any]:
        # Save the current iteration count and pending request in executor state for checkpointing.
        return {
            "iteration": self._iteration,
            "pending_request": self._pending_request,
            "pending_request_id": self._pending_request_id,
        }

    @override
    async def on_checkpoint_restore(self, state: dict[str, Any]) -> None:
        # Restore the iteration count and pending request from executor state during checkpoint recovery.
        self._iteration = state.get("iteration", 0)
        self._pending_request = state.get("pending_request")
        self._pending_request_id = state.get("pending_request_id")



def prompt_for_responses(requests: dict[str, HumanApprovalRequest]) -> dict[str, str]:
    """Interactive CLI prompt for any live RequestInfo requests."""

    responses: dict[str, str] = {}
    for request_id, request in requests.items():
        print("\n=== Human approval needed ===")
        print(f"request_id: {request_id}")
        print(f"Iteration: {request.iteration}")
        print(request.prompt)
        print("Draft: \n---\n" + request.draft + "\n---")
        response = input("Type 'approve' or enter revision guidance (or 'exit' to quit): ").strip()
        if response.lower() == "exit":
            raise SystemExit("Stopped by user.")
        responses[request_id] = response

    return responses


async def run_interactive_session(
    workflow: Workflow,
    initial_message: str | None = None,
    checkpoint_id: str | None = None,
) -> str:
    """Run the workflow until it either finishes or pauses for human input."""

    requests: dict[str, HumanApprovalRequest] = {}
    responses: dict[str, str] | None = None
    completed_output: str | None = None

    while True:
        if responses:
            event_stream = workflow.run(stream=True, responses=responses)
            requests.clear()
            responses = None
        else:
            if initial_message:
                print(f"\nStarting workflow with brief: {initial_message}\n")
                event_stream = workflow.run(message=initial_message, stream=True)
            elif checkpoint_id:
                print("\nStarting workflow from checkpoint...\n")
                event_stream = workflow.run(checkpoint_id=checkpoint_id, stream=True)
            else:
                raise ValueError("Either initial_message or checkpoint_id must be provided")

        async for event in event_stream:
            if event.type == "status":
                print(event)
            elif event.type == "output":
                # Only treat string outputs as final; AgentResponseUpdate is intermediate
                if isinstance(event.data, str):
                    completed_output = event.data
                    print(f"[DEBUG] Final output (string): {event.data[:50]}..." if len(str(event.data)) > 50 else f"[DEBUG] Final output: {event.data}")
                else:
                    print(f"[DEBUG] Intermediate output event: {type(event.data).__name__}")
            elif event.type == "request_info":
                print(f"[DEBUG] Request info event: {type(event.data).__name__}")
                if isinstance(event.data, HumanApprovalRequest):
                    requests[event.request_id] = event.data
                else:
                    raise ValueError(f"Unexpected request data type: {type(event.data)}")
            else:
                print(f"[DEBUG] Event: {event.type}")

        if completed_output:
            break

        if requests:
            responses = prompt_for_responses(requests)
            continue

        # If we resumed from a checkpoint that was already past completion,
        # the workflow has nothing left to do. This is not an error.
        if checkpoint_id:
            print("Workflow already completed at this checkpoint. Select a checkpoint marked [AWAITING HUMAN RESPONSE] to resume.")
            return "Workflow already completed at this checkpoint."

        raise RuntimeError("Workflow stopped without completing or requesting input")

    return completed_output


async def main() -> None:
    """Entry point used by both the initial run and subsequent resumes."""

    import json

    storage = FileCheckpointStorage(
        storage_path=TEMP_DIR,
        allowed_checkpoint_types=["__main__:HumanApprovalRequest"],
    )
    # Create workflow executors
    writer_agent = Agent(
        client=get_foundry_client(),
        instructions="Write concise, warm release notes that sound human and helpful.",
        name="writer",
    )
    writer = AgentExecutor(writer_agent)
    review_gateway = ReviewGateway(id="review_gateway", writer_id="writer")
    prepare_brief = BriefPreparer(id="prepare_brief", agent_id="writer")

    def build_workflow() -> Workflow:
        wb = (
            WorkflowBuilder(name="coffee_grinder_workflow", max_iterations=6, start_executor=prepare_brief, checkpoint_storage=storage, output_from=[review_gateway])
            .add_edge(prepare_brief, writer)
            .add_edge(writer, review_gateway)
            .add_edge(review_gateway, writer)  # revisions loop
        )
        return wb.build()

    # Check for existing checkpoints with pending human responses
    pending_cps = []
    checkpoint_files = list(TEMP_DIR.glob("*.json"))
    for cp_file in checkpoint_files:
        try:
            with open(cp_file, 'r') as f:
                cp_data = json.load(f)
            if cp_data.get('pending_request_info_events'):
                pending_cps.append({
                    'checkpoint_id': cp_file.stem,
                    'iteration': cp_data.get('iteration_count', 0),
                    'timestamp': cp_data.get('timestamp', ''),
                })
        except Exception:
            pass
    pending_cps.sort(key=lambda x: x['timestamp'])

    # If there are pending checkpoints, offer to resume
    if pending_cps:
        print(f"\nFound {len(pending_cps)} checkpoint(s) awaiting human response:")
        for idx, cp in enumerate(pending_cps):
            print(f"  [{idx}] id={cp['checkpoint_id']} iter={cp['iteration']}")

        selection = input("\nResume from checkpoint? (Enter index, or 'new' to start fresh): ").strip()  # noqa: ASYNC250

        if selection.lower() != "new":
            # Default to latest pending checkpoint
            try:
                idx = int(selection) if selection else len(pending_cps) - 1
            except ValueError:
                idx = len(pending_cps) - 1

            if 0 <= idx < len(pending_cps):
                chosen = pending_cps[idx]
                print(f"\nResuming from checkpoint: {chosen['checkpoint_id']}")

                # Reset executor state before resume
                review_gateway._pending_request = None
                review_gateway._pending_request_id = None
                review_gateway._iteration = 0

                workflow = build_workflow()
                result = await run_interactive_session(workflow, checkpoint_id=chosen['checkpoint_id'])
                print(f"Workflow completed with: {result}")
                return
            else:
                print("Index out of range; starting fresh.")

    # Start fresh: clean up old checkpoints
    for file in TEMP_DIR.glob("*.json"):
        file.unlink()

    workflow = build_workflow()

    brief = (
        "Introduce our limited edition smart coffee grinder. Mention the $249 price, highlight the "
        "sensor that auto-adjusts the grind, and invite customers to pre-order on the website."
    )

    print("Running workflow (human approval required)...")
    result = await run_interactive_session(workflow, initial_message=brief)
    print(f"Workflow completed with: {result}")


if __name__ == "__main__":
    asyncio.run(main())