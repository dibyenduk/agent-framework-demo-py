"""Shared configuration helpers for all demo notebooks.

Uses Microsoft Agent Framework with FoundryChatClient as the primary provider.
"""

import os
from dotenv import load_dotenv
from azure.identity import AzureCliCredential, DefaultAzureCredential

load_dotenv()

_credential = None
_client = None


def get_env(key: str, required: bool = True) -> str:
    """Return an environment variable or raise if required and missing."""
    value = os.environ.get(key, "")
    if required and (not value or value.startswith("<")):
        raise EnvironmentError(
            f"Environment variable '{key}' is not set. "
            f"Please update your .env file — see .env.template for guidance."
        )
    return value


def get_credential():
    """Return a cached AzureCliCredential (requires `az login`)."""
    global _credential
    if _credential is None:
        _credential = AzureCliCredential()
    return _credential    


def get_foundry_client():
    """Return a cached FoundryChatClient pointed at your Foundry project."""
    global _client
    if _client is None:
        from agent_framework.foundry import FoundryChatClient

        _client = FoundryChatClient(
            project_endpoint=get_env("AZURE_AI_PROJECT_ENDPOINT_FULL"),
            model=get_env("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
            credential=get_credential(),
        )
    return _client
