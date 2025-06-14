"""
Export functionality for chat history.
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple


def export_chat_to_json(
    conversation_history: List[Dict], filepath: str
) -> Tuple[bool, Optional[str]]:
    """
    Export chat history to a JSON file.

    Args:
        conversation_history: List of conversation messages
        filepath: Path to save the JSON file

    Returns:
        Tuple of (success, error_message)
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "conversation": conversation_history,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        logging.info(f"Chat history exported to JSON: {filepath}")
        return True, None
    except Exception as e:
        error_msg = f"Failed to export chat history to JSON: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return False, error_msg


def export_chat_to_text(
    conversation_history: List[Dict], filepath: str
) -> Tuple[bool, Optional[str]]:
    """
    Export chat history to a text file.

    Args:
        conversation_history: List of conversation messages
        filepath: Path to save the text file

    Returns:
        Tuple of (success, error_message)
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            for msg in conversation_history:
                role = "You" if msg["role"] == "user" else msg.get("model", "AI")
                f.write(f"{role}: {msg['content']}\n\n")
        logging.info(f"Chat history exported to text: {filepath}")
        return True, None
    except Exception as e:
        error_msg = f"Failed to export chat history to text: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return False, error_msg


def export_chat_to_markdown(
    conversation_history: List[Dict], filepath: str
) -> Tuple[bool, Optional[str]]:
    """
    Export chat history to a Markdown file.

    Args:
        conversation_history: List of conversation messages
        filepath: Path to save the Markdown file

    Returns:
        Tuple of (success, error_message)
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(
                f"# Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            for msg in conversation_history:
                role = "You" if msg["role"] == "user" else msg.get("model", "AI")
                f.write(f"## {role}\n\n{msg['content']}\n\n")

        logging.info(f"Chat history exported to Markdown: {filepath}")
        return True, None
    except Exception as e:
        error_msg = f"Failed to export chat history to Markdown: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return False, error_msg


def export_chat(
    conversation_history: List[Dict], filepath: str
) -> Tuple[bool, Optional[str]]:
    """
    Export chat history based on file extension.

    Args:
        conversation_history: List of conversation messages
        filepath: Path to save the file

    Returns:
        Tuple of (success, error_message)
    """
    if not conversation_history:
        return False, "No chat history to export"

    _, ext = os.path.splitext(filepath)
    ext = ext.lower()

    if ext == ".json":
        return export_chat_to_json(conversation_history, filepath)
    elif ext == ".txt":
        return export_chat_to_text(conversation_history, filepath)
    elif ext == ".md":
        return export_chat_to_markdown(conversation_history, filepath)
    else:
        # Default to JSON if extension not recognized
        logging.warning(
            f"Unrecognized file extension '{ext}', defaulting to JSON format"
        )
        return export_chat_to_json(conversation_history, filepath)


def import_chat(filename: str) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
    """
    Import chat history from a file.

    Args:
        filename: Input filename

    Returns:
        (success, conversation_history, error_message)
    """
    try:
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".json":
            # Handle JSON import
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Handle different JSON formats
            if isinstance(data, dict) and "conversation" in data:
                # Our standard export format
                return True, data["conversation"], None
            elif isinstance(data, list):
                # Simple list of messages
                return True, data, None
            else:
                return False, [], "Unrecognized JSON format"

        elif ext == ".md":
            # Simple handling of markdown - this could be enhanced
            messages = []
            current_role = None
            current_content = []

            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                if line.startswith("### User:"):
                    # Save previous message if exists
                    if current_role:
                        messages.append(
                            {
                                "role": current_role,
                                "content": "".join(current_content).strip(),
                            }
                        )
                    # Start new user message
                    current_role = "user"
                    current_content = []
                elif line.startswith("### Assistant:"):
                    # Save previous message if exists
                    if current_role:
                        messages.append(
                            {
                                "role": current_role,
                                "content": "".join(current_content).strip(),
                            }
                        )
                    # Start new assistant message
                    current_role = "assistant"
                    current_content = []
                else:
                    # Add to current message content
                    current_content.append(line)

            # Add the last message if any
            if current_role and current_content:
                messages.append(
                    {"role": current_role, "content": "".join(current_content).strip()}
                )

            return True, messages, None

        elif ext == ".txt":
            # Simple format: alternating user/assistant messages
            messages = []
            lines = []

            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()

            current_role = "user"  # Assume first message is from user
            current_content = []

            for line in lines:
                stripped = line.strip()
                # Simple heuristic: blank lines might separate messages
                if not stripped and current_content:
                    messages.append(
                        {
                            "role": current_role,
                            "content": "".join(current_content).strip(),
                        }
                    )
                    # Toggle role for next message
                    current_role = "assistant" if current_role == "user" else "user"
                    current_content = []
                else:
                    current_content.append(line)

            # Add the last message if any
            if current_content:
                messages.append(
                    {"role": current_role, "content": "".join(current_content).strip()}
                )

            return True, messages, None

        else:
            return False, [], f"Unsupported file extension: {ext}"

    except Exception as e:
        logging.error(f"Error importing chat: {str(e)}", exc_info=True)
        return False, [], str(e)
