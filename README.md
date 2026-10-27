# Running the Agent Framework Samples

## Prerequisites

- Python 3.10 or later.
- VS Code with the Python and Jupyter extensions, or a browser with Jupyter Notebook.
- For Azure-backed samples: Azure CLI, a Microsoft Foundry project with a deployed
  model, and permission to use that project and any tools required by the sample.
  Model calls and other Azure services can incur charges.

Run the commands below in Windows PowerShell from the repository root.

## 1. Create a virtual environment and install dependencies

A virtual environment is recommended to keep the sample dependencies separate
from other Python projects. It is not mandatory if you already have a compatible
environment, but the commands below assume the project's `.venv`.

Create the environment once:

```powershell
python -m venv .venv
```

Install the dependencies from [requirements.txt](requirements.txt):

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

These commands use the virtual environment directly, so activation is not
required. If you prefer to activate it in a terminal:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the explicit `.venv` executable paths shown
in this guide instead. Before updating dependencies in an existing environment,
shut down notebook kernels to avoid Windows file-lock errors.

## 2. Configure Azure-backed samples

Create `.env` from [.env.template](.env.template) if you do not already have one:

```powershell
if (-not (Test-Path .\.env)) {
    Copy-Item .\.env.template .\.env
}
```

Edit `.env` and replace the placeholders with your own configuration:

- `AZURE_AI_PROJECT_ENDPOINT_FULL`: the full Foundry project endpoint.
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`: your deployed model's deployment name.
- Set other values from the template when required by the notebook you choose.

Authenticate using the Azure account that has access to the project:

```powershell
az login
```

Keep `.env` private. Do not commit credentials or sensitive notebook outputs.
Restart the notebook kernel after changing environment settings.

The local [basic workflow sample](05_1workflow_basic.ipynb) does not require
Azure configuration or authentication.

## 3. Run the notebooks

### Option A: VS Code

1. Open the repository folder in VS Code, not just an individual notebook.
2. Open the sample `.ipynb` file.
3. Use **Select Kernel > Python Environments** and select
   `.\.venv\Scripts\python.exe`.
4. Read the sample's setup notes, then run its cells from top to bottom. Respond
   to any approval or input prompts when requested.

If the environment is missing from the picker, run **Python: Select Interpreter**
from the Command Palette, select the same executable, and select the notebook
kernel again.

### Option B: Jupyter Notebook

Register a named kernel once, then start Jupyter from the repository root:

```powershell
.\.venv\Scripts\python.exe -m ipykernel install --user --name agent-framework-demo-py --display-name "Agent Framework Demo (.venv)"
.\.venv\Scripts\python.exe -m notebook
```

Open a sample in the browser, select **Agent Framework Demo (.venv)** as its
kernel, and run the cells in order. Keep the terminal running while using Jupyter.

### Sample-specific setup

- Tool, Foundry IQ, and Foundry memory notebooks may require additional service
  configuration or permissions. Review their setup cells and resource names
  before running; replace resource-specific settings with your own.
- In the [conversation-history sample](04_agent_conv_history_provider.ipynb),
  run Parts A-D for the file-backed example. Skip the final Cosmos section,
  which is marked **Not working** and is not a runnable part of the sample.
- Use non-sensitive demo inputs. Conversation history and checkpoint files store
  plaintext messages locally.

## 4. Run the Python checkpoint sample

Run [09_agent_checkpoint.py](09_agent_checkpoint.py) in a terminal, not as a
notebook. Complete the environment setup, Azure configuration, and `az login`
steps above, then run:

```powershell
.\.venv\Scripts\python.exe .\09_agent_checkpoint.py
```

To demonstrate pausing and resuming:

1. If a saved-run menu appears, enter `new` to start a separate run.
2. Wait for the human-approval prompt and review the generated draft.
3. Enter `pause` or `exit` at that prompt to save the pending approval and exit.
4. Run the same command again. Select the saved run's index, or press Enter to
   resume the most recent pending run.
5. Enter `approve` to finish, or enter revision instructions to generate another
   draft for review. Blank input does not approve.

Checkpoints are retained under `tmp\checkpoints_hitl\run-<UUID>`. Completed runs
keep their history but are not offered for resume. Pause at the approval prompt
rather than interrupting an active model call.
