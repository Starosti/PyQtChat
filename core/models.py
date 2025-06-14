"""
Model management for the PyQtChat application.
"""

import logging
from typing import Dict, List, Optional
from core.settings import settings_manager


class ModelManager:
    """Manages available AI models and providers."""

    def __init__(self):
        """Initialize with default models and load custom models from settings."""
        # Available models by provider
        self.models = {
            "OpenAI": [
                "gpt-4o-mini",
                "gpt-4o",
                "gpt-4.1-mini",
                "gpt-4.1-nano",
                "gpt-4.1",
            ],
            "Anthropic": [
                "claude-3-7-sonnet-20250219",
                "claude-sonnet-4-20250514",
                "claude-opus-4-20250514",
            ],
            "Google": [
                "gemini/gemini-2.5-pro-preview-05-06",
                "gemini/gemini-2.5-flash-preview-05-20",
            ],
            "OpenRouter": [
                "openrouter/microsoft/wizardlm-2-8x22b",
                "openrouter/meta-llama/llama-4-maverick",
                "openrouter/meta-llama/llama-3-70b-instruct",
                "openrouter/openai/gpt-4.1-mini",
                "openrouter/google/gemini-2.5-flash-preview-05-20",
                "openrouter/openai/gpt-4o-mini",
            ],
            "Other": ["ollama/llama2", "together_ai/meta-llama/Llama-2-7b-chat-hf"],
        }

        # Load custom models
        self.load_custom_models()

    def load_custom_models(self) -> None:
        """Load custom models from settings."""
        custom_models = settings_manager.get_custom_models()
        if custom_models:
            self.models["Custom"] = custom_models
            logging.info(f"Loaded {len(custom_models)} custom models")
        elif "Custom" in self.models:
            # Remove custom category if no models
            del self.models["Custom"]

    def get_providers(self) -> List[str]:
        """Get list of all available providers."""
        return list(self.models.keys())

    def get_models_for_provider(self, provider: str) -> List[str]:
        """Get all models for a specific provider."""
        if provider in self.models:
            return self.models[provider]
        return []

    def get_all_models(self) -> Dict[str, List[str]]:
        """Get all models organized by provider."""
        return self.models

    def is_valid_model(self, model_name: str) -> bool:
        """Check if a model name is valid."""
        for provider, models in self.models.items():
            if model_name in models:
                return True
        return False

    def get_provider_for_model(self, model_name: str) -> Optional[str]:
        """Get the provider for a specific model."""
        for provider, models in self.models.items():
            if model_name in models:
                return provider
        return None

    def reload(self) -> None:
        """Reload models (especially custom models)."""
        self.load_custom_models()


# Create a singleton instance
model_manager = ModelManager()
