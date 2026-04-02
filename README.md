# 🤖 Agent Framework Demo — Microsoft Foundry

A progressive demo showcasing the **Microsoft Agent Framework** with Foundry as the provider, through 5 Jupyter notebooks.

## Packages Used

| Package | Purpose | Status |
|---------|---------|--------|
| `azure-ai-projects` | Foundry Project SDK — register agents, enable tracing | GA (v2.x) |
| `agent-framework-foundry` | Agent Framework + Foundry provider (`FoundryChatClient`, `FoundryAgent`) | Preview |
| `azure-ai-agentserver-agentframework` | Host Agent Framework agents as containers on Foundry | Preview |
| `azure-ai-evaluation` | Batch evaluation with quality & safety metrics | GA |
| `azure-identity` | Azure authentication (`AzureCliCredential`) | GA |

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

## Notebooks

| # | Notebook | Agent Framework Features | Required .env |
|---|----------|--------------------------|---------------|
| 01 | [Basic Agent](01_basic_agent.ipynb) | `AIProjectClient` → `FoundryAgent`, traces in portal, sessions, streaming | `AZURE_AI_PROJECT_ENDPOINT`, `AZURE_AI_PROJECT_ENDPOINT_FULL`, `AZURE_AI_MODEL_DEPLOYMENT_NAME` |
| 02 | [Tool-Augmented](02_tool_augmented_agent.ipynb) | Code Interpreter, File Search, Web Search, `@tool` decorator | `AZURE_AI_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME` |
| 03 | [Enterprise Integration](03_enterprise_integration.ipynb) | Hosted MCP, `FoundryAgent`, `agent.as_tool()` | + `MCP_SERVER_URL` (optional) |
| 04 | [Multi-Agent Workflows](04_multi_agent_orchestration.ipynb) | `SequentialBuilder`, `WorkflowBuilder`, sub-workflows, `workflow.as_agent()` | Same as 02 |
| 05 | [Evaluate & Deploy](05_evaluate_and_deploy.ipynb) | Batch evaluation, `from_agent_framework()` hosted deploy | + `AZURE_AI_PROJECT` (optional) |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Microsoft Agent Framework                       │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │   Agent    │  │  Tools   │  │ Sessions │  │  Workflows   │  │
│  │ (core)    │  │ Function │  │ Memory   │  │ Sequential   │  │
│  │           │  │ CodeInt  │  │ State    │  │ Graph-based  │  │
│  │           │  │ FileSrch │  │          │  │ Sub-workflows│  │
│  │           │  │ WebSrch  │  │          │  │              │  │
│  │           │  │ MCP      │  │          │  │              │  │
│  └─────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│        └──────────────┴─────────────┴───────────────┘          │
│                             │                                    │
│                    FoundryChatClient                             │
│                    FoundryAgent                                  │
└─────────────────────┬───────────────────────────────────────────┘
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
├── .gitignore
├── requirements.txt           # Python dependencies
├── README.md
├── utils/
│   ├── __init__.py
│   └── config.py              # FoundryChatClient setup
├── assets/
│   ├── product_info.md        # Sample product catalog (File Search)
│   └── sample_sales.csv       # Sample sales data (Code Interpreter)
├── 01_basic_agent.ipynb
├── 02_tool_augmented_agent.ipynb
├── 03_enterprise_integration.ipynb
├── 04_multi_agent_orchestration.ipynb
└── 05_evaluate_and_deploy.ipynb
```

## References

- [Microsoft Agent Framework Overview](https://learn.microsoft.com/agent-framework/overview/)
- [Agent Framework — Foundry Provider](https://learn.microsoft.com/agent-framework/agents/providers/microsoft-foundry)
- [Agent Framework — Tools](https://learn.microsoft.com/agent-framework/agents/tools/)
- [Agent Framework — Workflows](https://learn.microsoft.com/agent-framework/workflows/)
- [Hosted Agent Deployment](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent)
- [Agent Evaluation](https://learn.microsoft.com/azure/foundry/how-to/develop/evaluate-agents)
- [GitHub: microsoft/agent-framework](https://github.com/microsoft/agent-framework)
