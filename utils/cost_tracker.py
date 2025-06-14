"""
Utility for tracking and calculating costs of AI model usage.
"""

import logging

# Try to import litellm's model_cost with more descriptive error handling
try:
    from litellm import model_cost
    from litellm.utils import token_counter

    COST_TRACKING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"LiteLLM not installed or model_cost not available: {e}")
    logging.info(
        "Cost tracking will not be available. To enable cost tracking, install LiteLLM: pip install litellm"
    )
    model_cost = {}
    COST_TRACKING_AVAILABLE = False
except Exception as e:
    logging.error(f"Unexpected error importing LiteLLM cost tracking: {e}")
    model_cost = {}
    COST_TRACKING_AVAILABLE = False


def get_model_cost_display(model_name: str) -> str:
    """
    Generate a display string for model cost information.

    Args:
        model_name: The name of the model to get cost for

    Returns:
        A formatted string showing cost information
    """
    if not COST_TRACKING_AVAILABLE:
        return "Cost tracking unavailable<br><small>Install LiteLLM to enable: pip install litellm</small>"

    try:

        if model_name in model_cost:
            model_info = model_cost[model_name]
            input_cost = model_info.get("input_cost_per_token", 0)
            output_cost = model_info.get("output_cost_per_token", 0)

            # Convert to cost per million tokens for easier reading
            input_per_million = input_cost * 1000000
            output_per_million = output_cost * 1000000

            return f"<b>Input:</b> ${input_per_million:.4f}/1M <br> <b>Output:</b> ${output_per_million:.4f}/1M"
        else:
            return f"Cost data not available for '{model_name}'<br><small>This may be a custom or newly released model. Some OpenRouter models costs can also be missing.</small>"
    except Exception as e:
        logging.error(f"Error getting cost display for model {model_name}: {e}")
        return "Error retrieving cost information"


def calculate_message_cost(
    model_name: str, token_count: int, is_input: bool = True
) -> float:
    """
    Calculate the cost of a message based on token count and model.

    Args:
        model_name: The name of the model used
        token_count: Number of tokens in the message
        is_input: Whether this is an input (user) or output (AI) message

    Returns:
        The calculated cost in dollars
    """
    if not COST_TRACKING_AVAILABLE:
        return 0.0

    try:
        model_info = model_cost[model_name]

        if is_input:
            cost_per_token = model_info.get("input_cost_per_token", 0)
        else:
            cost_per_token = model_info.get("output_cost_per_token", 0)

        return token_count * cost_per_token
    except Exception as e:
        logging.error(f"Error calculating cost for model {model_name}: {e}")
        return 0.0


def estimate_tokens(text: str, model: str) -> int:
    """
    Estimate the number of tokens in a text string for a specific model.

    Args:
        text (str): The input text string to analyze for token estimation
        model (str): The model identifier used to determine tokenization method
                    (e.g., 'gpt-3.5-turbo', 'gpt-4', etc.)
    """

    return token_counter(model=model, text=text)
