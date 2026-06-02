# 🤖 Agent Framework Demo — Microsoft Foundry

A progressive demo showcasing the **Microsoft Agent Framework** with Foundry as the provider, through 11 hands-on demos (notebooks + scripts) covering single-agent basics through advanced multi-agent orchestration, memory, checkpointing, and skills.

## Packages Used

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| `agent-framework-foundry` | 1.7.0 | Agent Framework + Foundry provider (`FoundryChatClient`, `FoundryAgent`) | GA |
| `agent-framework-orchestrations` | 1.0.0rc2 | Orchestration patterns (Sequential, Graph, GroupChat, HandOff) | RC |
| `azure-ai-projects` | 2.1.0 | Foundry Project SDK — register agents, enable tracing | GA |
| `azure-identity` | 1.25.3 | Azure authentication (`AzureCliCredential`) | GA |
| `python-dotenv` | 1.2.2 | Environment variable management | GA |
| `jupyter` | 1.1.1 | Jupyter notebook environment | GA |
| `ipykernel` | 7.2.0 | IPython kernel for Jupyter | GA |
| `ipywidgets` | 8.1.8 | Interactive widgets for notebooks | GA |
| `pandas` | 3.0.3 | Data manipulation & analysis | GA |
| `matplotlib` | 3.10.9 | Data visualization (for notebooks 02+) | GA |

## Quick Start

```bash
# 1. Navigate to this folder
cd agent-framework-demo-py

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.template .env
# Edit .env with your Foundry project endpoint and model name

# 5. Authenticate to Azure
az login

# 6. Open notebooks
jupyter notebook
```

## Notebooks & Demos

| # | File | Topic | Key Features |
|---|------|-------|--------------|
| 01 | [Basic Agent](01_basic_agent.ipynb) | Single agent basics | `Agent`, `FoundryChatClient`, multi-provider support, server-side tracing in Foundry portal |
| 02 | [Local Tools (Function Calling)](02_agent_tools_functioncall.ipynb) | Custom tools | `@tool` decorator, `FunctionTool` schema, local tool binding, traced tool calls |
| 03 | [Built-in Tools](03_agent_tools_builtin.ipynb) | Platform tools | `CodeInterpreterTool`, `FileSearchTool`, `WebSearchTool`, server-side execution |
| 04 | [MCP Tools](04_agent_tools_mcp.ipynb) | External integrations | Model Context Protocol (MCP), `get_mcp_tool()`, tool approval modes, secure external data |
| 05 | [Multi-Agent: Graph](05_multi_agent_orchestration_graph.ipynb) | Graph orchestration | `GraphBuilder`, complex multi-agent coordination |
| 06 | [Multi-Agent: Sequential](06_multi_agent_orchestration_simple.ipynb) | Sequential orchestration | `SequentialBuilder`, linear agent handoff, message streaming |
| 07 | [Advanced Orchestration](07_orchestrations_advanced.ipynb) | GroupChat & HandOff | GroupChat with orchestrator moderation, HandOff mesh topology, termination conditions |
| 08 | [Human in the Loop](08_human_in_the_loop.ipynb) | Human approval | `AgentExecutor`, `AgentExecutorRequest/Response`, human approval workflows |
| 09 | [Checkpointing](09_agent_checkpoint.py) | Pause & resume | `FileCheckpointStorage`, checkpoint persistence, recovery, pre-supplied responses |
| 10 | [Foundry Memory](10_agent_foundrymemory.ipynb) | Persistent memory | `MemorySearchPreviewTool`, `MemoryStoreDefaultDefinition`, cross-session memory, per-user scoping |
| 11 | [Skills](11_agent_skill.ipynb) | File-based skills | Skill definitions, subprocess execution, modular agent capabilities |

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
