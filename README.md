# 🤖 Agent Framework Demo — Microsoft Foundry

A progressive demo showcasing the **Microsoft Agent Framework** with Foundry as the provider, through 11 hands-on demos (notebooks + scripts) covering single-agent basics through advanced multi-agent orchestration, memory, checkpointing, and skills.

## Packages Used

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| `agent-framework-core` | 1.22.0 | Shared agent and workflow APIs | GA |
| `agent-framework-foundry` | 1.15.0 | Agent Framework + Foundry provider (`FoundryChatClient`, `FoundryAgent`) | GA |
| `agent-framework-orchestrations` | 1.3.2 | Orchestration patterns (Sequential, Graph, GroupChat, HandOff) | GA |
| `azure-ai-projects` | 2.7.0 | Foundry Project SDK — register agents, enable tracing | GA |
| `azure-identity` | 1.25.3 | Azure authentication (`AzureCliCredential`) | GA |
| `python-dotenv` | 1.2.2 | Environment variable management | GA |
| `jupyter` | 1.1.1 | Jupyter notebook environment | GA |
| `ipykernel` | 7.2.0 | IPython kernel for Jupyter | GA |
| `ipywidgets` | 8.1.8 | Interactive widgets for notebooks | GA |
| `pandas` | 2.3.3 | Data manipulation & analysis | GA |
| `matplotlib` | 3.10.9 | Data visualization (for notebooks 02+) | GA |

The Agent Framework packages are pinned to compatible stable releases available
from the configured Microsoft package mirror; their version numbers do not need
to match. Core 1.23.0 and orchestrations 1.4.0 are not yet available on that mirror.
Foundry 1.15.0 requires
`agent-framework-core>=1.22.0,<2` and `azure-ai-projects>=2.2.0,<2.8.0`.
Orchestrations 1.3.2 requires `agent-framework-core>=1.19.0,<2`.
The Project SDK is therefore pinned to 2.7.0, the latest compatible stable
release, rather than the incompatible 2.9.0.

Pandas is pinned to 2.3.3 to remain compatible with `azure-ai-evaluation` 1.16.2
when installed alongside these demos; that package requires pandas below 3.0.0.

## Quick Start

```bash
# 1. Navigate to this folder
cd agent-framework-demo-py

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate  # macOS/Linux

# 3. Install dependencies
python -m pip install --upgrade -r requirements.txt
python -m pip check

# 4. Configure environment
cp .env.template .env
# Edit .env with your Foundry project endpoint and model name

# 5. Authenticate to Azure
az login

# 6. Open notebooks
jupyter notebook
```

On Windows, shut down notebook kernels before upgrading an existing environment.
Running kernels can lock native dependencies and cause `WinError 5` during
installation. After shutting them down, rerun the install and `pip check` commands.

## Notebooks & Demos

| # | File | Topic | Key Features |
|---|------|-------|--------------|
| 01 | [Basic Agent](01_basic_agent.ipynb) | Single agent basics | `Agent`, `FoundryChatClient`, multi-provider support, server-side tracing in Foundry portal |
| 02 | [Local Tools (Function Calling)](02_agent_tools_functioncall.ipynb) | Custom tools | `@tool` decorator, `FunctionTool` schema, local tool binding, traced tool calls |
| 03 | [Built-in Tools](03_agent_tools_builtin.ipynb) | Platform tools | `CodeInterpreterTool`, `FileSearchTool`, `WebSearchTool`, server-side execution |
| 03 | [Foundry IQ](03_agent_tools_foundryiq.ipynb) | Multi-source RAG | Hosted knowledge-base MCP tool, Australian grants index and public web retrieval, answer citations and source activity |
| 04 | [MCP Tools](04_agent_tools_mcp.ipynb) | External integrations | Model Context Protocol (MCP), `get_mcp_tool()`, tool approval modes, secure external data |
| 04 | [Agent Memory](04_agent_memory.ipynb) | Session memory | `ContextProvider`, before/after hooks, per-session name memory |
| 04 | [Conversation History Provider](04_agent_convhistory_provider.ipynb) | File-backed history | `FileHistoryProvider`, two-turn chat without tools, raw and formatted JSONL inspection; local logs in Git-ignored `sessions/` |
| 05 | [Basic Workflow](05_workflow_basic.ipynb) | Executors & edges | `@executor`, `WorkflowBuilder`, message routing and workflow outputs; runs locally without Azure |
| 05 | [Multi-Agent: Graph](05_multi_agent_orchestration_graph.ipynb) | Graph orchestration | `GraphBuilder`, complex multi-agent coordination |
| 06 | [Multi-Agent: Sequential](06_multi_agent_orchestration_simple.ipynb) | Sequential orchestration | `SequentialBuilder`, linear agent handoff, message streaming |
| 07 | [Advanced Orchestration](07_orchestrations_advanced.ipynb) | GroupChat & HandOff | GroupChat with orchestrator moderation, HandOff mesh topology, termination conditions |
| 07 | [Magentic Orchestration](07_orchestrations_magentic.ipynb) | Manager-led planning | `MagenticBuilder`, Planner and Reviewer, visible planning/progress events, bounded coordination, manager synthesis |
| 08 | [Human in the Loop](08_human_in_the_loop.ipynb) | Human approval | `AgentExecutor`, `AgentExecutorRequest/Response`, human approval workflows |
| 09 | [Checkpointing](09_agent_checkpoint.py) | Pause & resume | `FileCheckpointStorage`, separate run histories, restart at human approval without regenerating the saved draft |
| 10 | [Foundry Memory](10_agent_foundrymemory.ipynb) | Persistent memory | `MemorySearchPreviewTool`, `MemoryStoreDefaultDefinition`, cross-session memory, per-user scoping |
| 11 | [Skills](11_agent_skill.ipynb) | File-based skills | Skill definitions, subprocess execution, modular agent capabilities |

### Magentic orchestration demo

Open [07_orchestrations_magentic.ipynb](07_orchestrations_magentic.ipynb), select
the project `.venv` kernel, and run all cells after configuring `.env` and
authenticating with `az login`. It uses the same `AZURE_AI_PROJECT_ENDPOINT_FULL`
and `AZURE_AI_MODEL_DEPLOYMENT_NAME` settings as the other orchestration notebooks.

The manager delegates a workshop plan to Planner, asks Reviewer to check timing
and costs, and synthesizes the final answer. Planning events, next-agent
instructions, and specialist responses are printed during execution. No tools,
new Azure resources, or interactive input are required; several billed model
calls are made. Rerun from Step 1 for a fresh team and workflow.

### Checkpoint demo: stop, restart, and approve

Run this **in a terminal**, using the project environment and the Foundry
configuration in `.env`. Authenticate with `az login` first:

```powershell
.\.venv\Scripts\python.exe .\09_agent_checkpoint.py
```

1. If a resume menu appears, enter `new` to start a separate demo run.
2. Wait for **Human approval needed** and inspect the draft. The script prints
   the saved checkpoint ID and run directory before asking for a decision.
3. Enter `pause` (or `exit`) at the approval prompt. The program exits normally,
   preserving the draft and pending approval. You can now close the terminal.
4. Run the same command again. Choose the displayed run index, or press Enter
   to select the most recently saved pending run.
5. The saved draft and review iteration reappear. Enter `approve` to complete
   the workflow. Restoring and approving the draft does **not** call the writer
   model again. To request a revision instead, enter instructions such as
   `Make it shorter and emphasize the price`; the writer produces a new draft
   that requires a new approval. The demo has a 20-superstep iteration limit.

At an approval prompt, blank input does **not** approve. Ctrl+C or EOF at a
prompt also preserves the checkpoint. Use `pause` at the approval prompt for
the most predictable stop/resume demonstration; interrupting during an active
model call is not the same as pausing at a completed checkpoint boundary.
At the initial run-selection menu, `exit` leaves all saved runs unchanged;
`new` starts a separate run without deleting earlier history.

**Why JSON files remain after approval:** the framework saves immutable
snapshots between workflow steps and when responses are applied. Approval
does not erase those historical files. New runs are isolated under
`tmp/checkpoints_hitl/run-<UUID>/`; only each run's **latest** checkpoint is
considered for resume. Once approved and completed, that latest checkpoint
has no pending approval, so the completed run is never offered again.
Previously created JSON files directly under `tmp/checkpoints_hitl/` are
treated as one legacy run: only the latest snapshot is considered. Older
legacy files cannot reliably identify separate runs, so they are not listed
individually as live approvals.

History is retained deliberately and excluded from Git. It contains plaintext
prompts, drafts and responses; do not use secrets in the demo. Remove a specific completed run's
folder manually only when you no longer need its history. The script never
automatically deletes existing checkpoints.

Offline regression tests (no Azure requests):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_agent_checkpoint.py -v
```

### Foundry IQ demo

The Foundry IQ notebook targets project `prj-foundry-demo-us-east-dev-001` on
`foundry-demo-us-east-resource` and reuses its `ausgrantssearchoemwx58vui7d`
Search connection. Demo knowledge base `ausgrants-demo-kb` has two new knowledge
sources: `ausgrants-demo-index` (the existing `grants-index-v2` index) and
`ausgrants-demo-web` (public web retrieval). The agent uses deployed model
`gpt-4.1-821390` and project-managed-identity MCP connection
`ausgrants-demo-kb-mcp`. Query planning uses the existing `gpt-4o` deployment.

Run with the project virtual environment and `az login`. The notebook verifies
the existing configuration, runs a cited agent answer, and offers an optional
additional retrieval to display source activity and reference URLs. Azure
inference, retrieval and public web usage are billable. The Search managed
identity was granted Cognitive Services OpenAI User on the Foundry resource
with approval; no API keys are stored in the notebook. Existing knowledge bases
and indexes were not changed. See the notebook for permissions and cleanup notes.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Microsoft Agent Framework                              │
│                                                                             │
│  ┌───────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────────────┐  │
│  │   Agent   │  │    Tools     │  │  Memory &  │  │   Orchestration    │  │
│  │  (core)   │  │  Function    │  │  State     │  │   Sequential       │  │
│  │           │  │  CodeInterp  │  │  Checkpoint│  │   Graph-based      │  │
│  │           │  │  FileSearch  │  │  Foundry   │  │   GroupChat        │  │
│  │           │  │  WebSearch   │  │  Memory    │  │   HandOff          │  │
│  │           │  │  MCP         │  │            │  │   Human-in-Loop    │  │
│  │           │  │  Skills      │  │            │  │                    │  │
│  └─────┬─────┘  └──────┬──────┘  └─────┬──────┘  └─────────┬──────────┘  │
│        └────────────────┴───────────────┴───────────────────┘             │
│                                  │                                         │
│                         FoundryChatClient                                  │
└──────────────────────────────────┬────────────────────────────────────────┘
                                   │
                           ┌───────▼────────┐
                           │ Microsoft      │
                           │ Foundry        │
                           │ (cloud)        │
                           └────────────────┘
```

## Prerequisites

1. **Azure subscription** with a [Microsoft Foundry](https://ai.azure.com) project
2. **Deployed model** (e.g., `gpt-4o-mini`, `gpt-4.1`)
3. **Python 3.10+**
4. **Azure CLI** (`az login` for authentication)

## Project Structure

```
agent-framework-demo-py/
├── .env.template              # Environment config template
├── requirements.txt           # Python dependencies
├── README.md
├── LICENSE                    # MIT License
├── utils/
│   ├── __init__.py
│   └── config.py              # FoundryChatClient + credential helpers
├── assets/
│   ├── product_info.md        # Sample product catalog (File Search)
│   └── sample_sales.csv       # Sample sales data (Code Interpreter)
├── skills/
│   ├── subprocess_script_runner.py   # Skill execution engine
│   └── file_based_skills/           # Modular skill definitions
│       └── skills/unit_converter/   # Example: unit conversion skill
├── tmp/
│   └── checkpoints_hitl/      # Checkpoint storage for HITL demos
├── 01_basic_agent.ipynb
├── 02_agent_tools_functioncall.ipynb
├── 03_agent_tools_builtin.ipynb
├── 04_agent_tools_mcp.ipynb
├── 05_multi_agent_orchestration_graph.ipynb
├── 06_multi_agent_orchestration_simple.ipynb
├── 07_orchestrations_advanced.ipynb
├── 08_human_in_the_loop.ipynb
├── 09_agent_checkpoint.py
├── 10_agent_foundrymemory.ipynb
└── 11_agent_skill.ipynb
```

## License

This project is licensed under the [MIT License](LICENSE).

## References

- [Microsoft Agent Framework Overview](https://learn.microsoft.com/agent-framework/overview/)
- [Agent Framework — Foundry Provider](https://learn.microsoft.com/agent-framework/agents/providers/microsoft-foundry)
- [Agent Framework — Tools](https://learn.microsoft.com/agent-framework/agents/tools/)
- [Agent Framework — Workflows](https://learn.microsoft.com/agent-framework/workflows/)
- [Hosted Agent Deployment](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent)
- [Agent Evaluation](https://learn.microsoft.com/azure/foundry/how-to/develop/evaluate-agents)
- [GitHub: microsoft/agent-framework](https://github.com/microsoft/agent-framework)
