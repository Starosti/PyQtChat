"""
Worker thread for handling AI chat requests.
"""

import os
import logging
from typing import List, Dict, Optional
from PyQt5.QtCore import QThread, pyqtSignal
from core.settings import settings_manager

try:
    from litellm import completion
    from litellm.utils import get_valid_models
except ImportError:
    logging.critical("LiteLLM not installed. Please run: pip install litellm")
    raise


class ChatWorker(QThread):
    """Worker thread for handling AI chat requests."""

    message_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal(str)  # Accepts a string for finish_reason

    def __init__(
        self,
        message: str,
        model: str,
        conversation_history: List[Dict],
    ):
        super().__init__()
        get_valid_models()
        self.message = message
        self.model = model
        self.conversation_history = conversation_history
        self.current_ai_message = ""  # Store the complete message
        self._should_stop = False  # Flag to signal worker to stop
        logging.info(f"Initialized ChatWorker with model: {model}")

    def run(self) -> None:
        """Execute the chat request."""
        try:
            logging.info(f"Starting chat request with model: {self.model}")
            max_tokens = settings_manager.get("max_tokens", 2000)

            # Build completion arguments
            completion_args = {
                "model": self.model,
                "messages": [
                    *self.conversation_history,
                    {"role": "user", "content": self.message},
                ],
                "stream": True,
                "max_tokens": max_tokens,
            }

            # Add API base if configured
            api_base_url = settings_manager.get("api_base_url", "")
            if api_base_url:
                completion_args["api_base"] = api_base_url
                logging.info(f"Using custom API base: {api_base_url}")

            response_stream = completion(**completion_args)
            finish_reason_overall = None

            for item_from_stream in response_stream:
                # Check if thread has been requested to stop
                if self._should_stop:
                    logging.info("ChatWorker received stop request, breaking loop")
                    break

                # Initialize to None to ensure it's clear if a valid chunk is found
                processed_chunk = None

                # Scenario 1: The item itself has 'choices'
                if hasattr(item_from_stream, "choices"):
                    processed_chunk = item_from_stream
                # Scenario 2: The item is a tuple, and one of its elements has 'choices'
                elif isinstance(item_from_stream, tuple):
                    for sub_item in item_from_stream:
                        if hasattr(sub_item, "choices"):
                            processed_chunk = sub_item
                            break  # Found the relevant part of the tuple

                # Now, operate on processed_chunk if it was successfully assigned
                if (
                    processed_chunk is not None
                    and hasattr(processed_chunk, "choices")
                    and processed_chunk.choices
                ):
                    # Ensure choices is not empty and is a list/sequence
                    if (
                        isinstance(processed_chunk.choices, list)
                        and len(processed_chunk.choices) > 0
                    ):
                        choice = processed_chunk.choices[0]

                        content_to_emit = None
                        if (
                            hasattr(choice, "delta")
                            and choice.delta
                            and hasattr(choice.delta, "content")
                        ):
                            content_to_emit = choice.delta.content

                        current_chunk_finish_reason = None
                        if hasattr(choice, "finish_reason"):
                            current_chunk_finish_reason = choice.finish_reason

                        if content_to_emit:
                            self.current_ai_message += (
                                content_to_emit  # Store complete message
                            )
                            self.message_received.emit(content_to_emit)

                        if current_chunk_finish_reason:
                            finish_reason_overall = current_chunk_finish_reason

            self.finished.emit(
                finish_reason_overall if finish_reason_overall else "stop"
            )
            logging.info(
                f"Chat request completed with finish reason: {finish_reason_overall}"
            )

        except ImportError as e:
            error_msg = "Required AI libraries are not installed. Please install LiteLLM: pip install litellm"
            logging.error(f"Import error in chat worker: {str(e)}")
            self.error_occurred.emit(error_msg)
            self.finished.emit("error")

        except Exception as e:
            error_str = str(e).lower()
            user_friendly_msg = str(e)

            # API Key related errors
            if any(
                key_term in error_str
                for key_term in ["bearer", "authentication", "unauthorized", "401"]
            ):
                user_friendly_msg = "API authentication failed. Please check your API key in Settings → Preferences and ensure it's valid and has sufficient credits."

            # Quota/billing errors
            elif any(
                quota_term in error_str
                for quota_term in ["quota", "billing", "insufficient", "exceeded"]
            ):
                user_friendly_msg = "You've exceeded your API quota or have insufficient credits. Please check your API account billing and usage."

            # Rate limiting errors
            elif any(
                rate_term in error_str
                for rate_term in ["rate limit", "429", "too many requests"]
            ):
                user_friendly_msg = "You've hit the API rate limit. Please wait a moment before sending another message."

            # Model availability errors
            elif any(
                model_term in error_str
                for model_term in [
                    "model not found",
                    "invalid model",
                    "model unavailable",
                ]
            ):
                user_friendly_msg = f"The model '{self.model}' is not available or accessible with your API key. Try selecting a different model."

            # Network/connection errors
            elif any(
                net_term in error_str
                for net_term in [
                    "connection",
                    "network",
                    "timeout",
                    "dns",
                    "unreachable",
                ]
            ):
                user_friendly_msg = "Connection error. Please check your connection and API keys, then try again."

            # Token limit errors
            elif any(
                token_term in error_str
                for token_term in [
                    "context length",
                    "token limit",
                    "max tokens",
                    "context_length_exceeded",
                ]
            ):
                user_friendly_msg = "The conversation is too long for this model. Try starting a new chat."

            # Content filtering errors
            elif any(
                content_term in error_str
                for content_term in ["content policy", "safety", "filtered", "blocked"]
            ):
                user_friendly_msg = "Your message was blocked by content safety filters. Please try rephrasing your request."

            # Server errors
            elif any(
                server_term in error_str
                for server_term in [
                    "500",
                    "502",
                    "503",
                    "504",
                    "internal server",
                    "bad gateway",
                    "service unavailable",
                ]
            ):
                user_friendly_msg = "The AI service is temporarily unavailable. Please try again in a few moments."

            # Timeout errors
            elif "timeout" in error_str:
                user_friendly_msg = "The request timed out. The AI service might be experiencing high demand. Please try again."

            logging.error(f"Error in chat worker: {str(e)}", exc_info=True)
            self.error_occurred.emit(user_friendly_msg)
            self.finished.emit("error")

    def stop_safely(self):
        """Request the worker to stop safely and clean up."""
        if not self.isRunning():
            return

        logging.info(f"Stopping worker safely for model: {self.model}")
        self._should_stop = True

        # Request thread to quit
        self.quit()

        # Wait for a reasonable time
        if not self.wait(3000):  # 3 seconds timeout
            logging.warning(
                f"Worker for model {self.model} did not terminate gracefully, forcing termination"
            )
            self.terminate()
            # Always wait after terminate to ensure thread is fully stopped
            self.wait()

        logging.info(f"Worker for model {self.model} stopped successfully")
