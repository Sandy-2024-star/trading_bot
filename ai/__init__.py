"""Optional local-AI integrations for the trading bot."""

try:
    from .local_llm import LocalLLMClient
except ImportError:  # pragma: no cover - fallback for script-style imports
    from ai.local_llm import LocalLLMClient

__all__ = ["LocalLLMClient"]
