import asyncio
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_framework import ChatResponse, ChatResponseUpdate, Content, ResponseStream, Workflow
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential


PROJECT_ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("checkpoint_demo", PROJECT_ROOT / "09_agent_checkpoint.py")
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load the checkpoint demo.")
demo = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = demo
spec.loader.exec_module(demo)


class CheckpointDemoTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="checkpoint-demo-test-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.model_calls = []
        self.stdout = io.StringIO()
        self.enterContext(patch("sys.stdout", self.stdout))

        client = FoundryChatClient(
            project_endpoint="https://example.services.ai.azure.com/api/projects/demo",
            model="test",
            credential=AzureCliCredential(),
        )
        self.enterContext(patch.object(demo, "get_foundry_client", return_value=client))
        calls = self.model_calls

        def model_response(client, messages, **kwargs):
            calls.append(messages)
            draft = f"Saved draft {len(calls)}."

            async def updates():
                yield ChatResponseUpdate(role="assistant", contents=[Content.from_text(draft)])

            return ResponseStream(updates(), finalizer=ChatResponse.from_updates)

        self.enterContext(patch.object(FoundryChatClient, "get_response", model_response))

    async def run_main(self, inputs):
        with patch("builtins.input", side_effect=inputs):
            await demo.main(self.root)

    async def test_pause_resume_approval_retains_history_but_hides_completed_run(self):
        await self.run_main(["pause"])
        pending = await demo.find_pending_runs(self.root)
        self.assertEqual(len(pending), 1)
        history = set(pending[0].storage_path.glob("*.json"))
        self.assertTrue(history)
        self.assertEqual(len(self.model_calls), 1)

        await self.run_main(["", "approve"])

        self.assertEqual(len(self.model_calls), 1, "Approval must not regenerate the saved draft.")
        self.assertEqual(await demo.find_pending_runs(self.root), [])
        self.assertTrue(all(path.exists() for path in history))
        self.assertIn("Approved draft:\nSaved draft 1.", self.stdout.getvalue())
        self.assertIn("will not be offered for resume", self.stdout.getvalue())

    async def test_new_run_preserves_other_pending_runs(self):
        await self.run_main(["pause"])
        first_run = (await demo.find_pending_runs(self.root))[0]
        history = set(first_run.storage_path.glob("*.json"))

        await self.run_main(["new", "exit"])

        pending = await demo.find_pending_runs(self.root)
        self.assertEqual(len(pending), 2)
        self.assertEqual(len({run.storage_path for run in pending}), 2)
        self.assertTrue(all(path.exists() for path in history))

    async def test_revision_iteration_survives_resume(self):
        await self.run_main(["Make it shorter.", "pause"])
        pending = (await demo.find_pending_runs(self.root))[0]
        request = next(iter(pending.checkpoint.pending_request_info_events.values())).data
        self.assertEqual(request.iteration, 2)
        self.assertEqual(request.draft, "Saved draft 2.")

        await self.run_main(["", "Add a call to action.", "approve"])

        self.assertEqual(len(self.model_calls), 3)
        self.assertEqual(await demo.find_pending_runs(self.root), [])
        self.assertIn("Iteration: 3", self.stdout.getvalue())
        self.assertIn("Approved draft:\nSaved draft 3.", self.stdout.getvalue())

    async def test_empty_input_does_not_approve(self):
        await self.run_main(["", "pause"])

        self.assertEqual(len(await demo.find_pending_runs(self.root)), 1)
        self.assertIn("Empty input does not approve", self.stdout.getvalue())
        self.assertNotIn("Workflow completed.", self.stdout.getvalue())

    async def test_interrupted_approval_prompt_preserves_checkpoint(self):
        for interrupt in (EOFError, KeyboardInterrupt):
            with self.subTest(interrupt=interrupt.__name__):
                root = self.root / interrupt.__name__
                with patch("builtins.input", side_effect=interrupt):
                    await demo.main(root)
                self.assertEqual(len(await demo.find_pending_runs(root)), 1)
        self.assertIn("Input interrupted", self.stdout.getvalue())

    async def test_invalid_menu_selection_is_not_silently_resumed(self):
        await self.run_main(["pause"])
        history = set(self.root.rglob("*.json"))

        await self.run_main(["not-an-index", "999", "exit"])

        self.assertEqual(history, set(self.root.rglob("*.json")))
        self.assertEqual(len(self.model_calls), 1)
        self.assertIn("Invalid selection", self.stdout.getvalue())
        self.assertIn("Index out of range", self.stdout.getvalue())

    async def test_legacy_flat_history_uses_only_latest_checkpoint(self):
        storage = demo.create_storage(self.root)
        with patch("builtins.input", return_value="pause"):
            await demo.run_interactive_session(
                demo.build_workflow(storage), storage, initial_message="Legacy draft"
            )
        paused = (await demo.find_pending_runs(self.root))[0]
        self.assertEqual(paused.storage_path, self.root)

        with patch("builtins.input", return_value="approve"):
            await demo.run_interactive_session(
                demo.build_workflow(storage), storage, checkpoint_id=paused.checkpoint.checkpoint_id
            )

        snapshots = await storage.list_checkpoints(workflow_name=demo.WORKFLOW_NAME)
        self.assertTrue(any(cp.pending_request_info_events for cp in snapshots))
        self.assertEqual(await demo.find_pending_runs(self.root), [])

    async def test_no_output_is_not_reported_as_success(self):
        async def no_events():
            if False:
                yield

        workflow = unittest.mock.Mock(spec=Workflow)
        workflow.run.return_value = ResponseStream(no_events())
        with self.assertRaisesRegex(RuntimeError, "without a final draft"):
            await demo.run_interactive_session(
                workflow, demo.create_storage(self.root), checkpoint_id="not-used"
            )

    async def test_stop_and_resume_in_separate_processes(self):
        worker = """
import asyncio
import importlib.util
import sys
from pathlib import Path
from agent_framework import ChatResponse, ChatResponseUpdate, Content, ResponseStream
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

spec = importlib.util.spec_from_file_location('checkpoint_demo', Path(sys.argv[1]))
demo = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = demo
spec.loader.exec_module(demo)
calls = 0
def model_response(self, messages, **kwargs):
    global calls
    calls += 1
    async def updates():
        yield ChatResponseUpdate(role='assistant', contents=[Content.from_text('Persisted across processes.')])
    return ResponseStream(updates(), finalizer=ChatResponse.from_updates)
FoundryChatClient.get_response = model_response
client = FoundryChatClient(
    project_endpoint='https://example.services.ai.azure.com/api/projects/demo',
    model='test', credential=AzureCliCredential())
demo.get_foundry_client = lambda: client
asyncio.run(demo.main(Path(sys.argv[2])))
print(f'MODEL_CALLS={calls}')
"""
        command = [
            sys.executable,
            "-c",
            worker,
            str(PROJECT_ROOT / "09_agent_checkpoint.py"),
            str(self.root),
        ]
        first = await asyncio.to_thread(
            subprocess.run, command, input="pause\n", capture_output=True, text=True,
            cwd=PROJECT_ROOT, timeout=60,
        )
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertIn("Paused safely", first.stdout)
        self.assertIn("MODEL_CALLS=1", first.stdout)

        second = await asyncio.to_thread(
            subprocess.run, command, input="\napprove\n", capture_output=True, text=True,
            cwd=PROJECT_ROOT, timeout=60,
        )
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertIn("Starting workflow from checkpoint", second.stdout)
        self.assertIn("Approved draft:\nPersisted across processes.", second.stdout)
        self.assertIn("MODEL_CALLS=0", second.stdout)
        self.assertEqual(await demo.find_pending_runs(self.root), [])


if __name__ == "__main__":
    unittest.main()
