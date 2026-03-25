"""
Development UI for the Life Coach System (Gradio).

This is a dev/testing interface — uses in-memory state and exposes debug tooling.
Not intended for production use.
Run: uv run python dev_ui.py
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import gradio as gr

from life_coach_system._logging import configure_logging, get_logger
from life_coach_system.config import settings
from life_coach_system.engine.coach import CoachAgent
from life_coach_system.exceptions import LifeCoachError
from life_coach_system.memory.logic.manager import MemoryManager
from life_coach_system.memory.schemas.session_state import SessionState
from life_coach_system.persistence.in_memory import InMemoryBackend
from life_coach_system.utils.evaluator import evaluate_conversation as evaluate_conv_llm
from life_coach_system.utils.evaluator import format_evaluation_results
from life_coach_system.utils.leaderboard_parser import (
    filter_checks_by_priority,
    parse_leaderboard_card,
)

log = get_logger(__name__)

# ===================================================================
# Global instances (singleton pattern)
# ===================================================================

storage = InMemoryBackend()
coach = CoachAgent(storage=storage)
memory_manager = MemoryManager()


# ===================================================================
# UI handling functions
# ===================================================================


def interact(message: str, history: list, user_id: str) -> tuple[list, dict, str]:
    """
    Main function handling interaction with coach.

    Args:
        message: User message
        history: Chat history (Gradio messages format: list of dicts)
        user_id: User ID

    Returns:
        Tuple: (updated_history, state_dict, export_json)
    """
    if not message or not message.strip():
        return history, {"status": "No message"}, ""

    # Use default user_id if empty
    if not user_id or not user_id.strip():
        user_id = settings.default_user_id

    # Get or create state — find active session for this user, or create new
    active = storage.find_active_session(user_id)
    if active is not None:
        state = SessionState(**active)
    else:
        state = memory_manager.create_empty_state(user_id)

    # Generate coach response
    try:
        response_text, updated_state, _is_closing = coach.respond(message, state)
    except LifeCoachError as e:
        error_msg = f"Error generating response: {str(e)}"
        log.error("interact_failed", error=str(e))
        return history, {"error": error_msg}, ""
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log.error("interact_unexpected", error=str(e))
        return history, {"error": error_msg}, ""

    # Save state (keyed by session_id)
    storage.save(updated_state.session_id, updated_state.model_dump())

    # Update Gradio history (messages format: list of dicts)
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response_text})

    # Prepare state visualization (dict for gr.JSON)
    state_dict = updated_state.model_dump()

    # Prepare export data (convert history to tuples for export)
    export_history = []
    for i in range(0, len(history) - 1, 2):
        if i + 1 < len(history):
            export_history.append(
                (history[i].get("content", ""), history[i + 1].get("content", ""))
            )

    export_data = {
        "user_id": user_id,
        "exported_at": datetime.now().isoformat(),
        "conversation": export_history,
        "state": updated_state.model_dump(),
    }
    export_json = json.dumps(export_data, indent=2, ensure_ascii=False)

    return history, state_dict, export_json


def reset_conversation(user_id: str) -> tuple[list, dict, str]:
    """
    Resets conversation (clears history and state).

    Args:
        user_id: User ID

    Returns:
        Tuple: (empty_history, message, empty_export)
    """
    if not user_id or not user_id.strip():
        user_id = settings.default_user_id

    # Delete all sessions for this user
    for summary in storage.list_sessions(user_id):
        storage.delete(summary["session_id"])

    return [], {"status": "State cleared"}, ""


def load_state_for_user(user_id: str) -> tuple[list, dict, str]:
    """
    Loads state for given user (to display when user_id changes).

    Args:
        user_id: User ID

    Returns:
        Tuple: (history, state_dict, export_json)
    """
    if not user_id or not user_id.strip():
        user_id = settings.default_user_id

    active = storage.find_active_session(user_id)
    if active is not None:
        state = SessionState(**active)

        # Reconstruct history for Gradio messages format (list of dicts)
        history = []
        for msg in state.conversation_history:
            history.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

        state_dict = state.model_dump()

        # Convert history to tuples for export
        export_history = []
        for i in range(0, len(history) - 1, 2):
            if i + 1 < len(history):
                export_history.append(
                    (history[i].get("content", ""), history[i + 1].get("content", ""))
                )

        export_data = {
            "user_id": user_id,
            "exported_at": datetime.now().isoformat(),
            "conversation": export_history,
            "state": state.model_dump(),
        }
        export_json = json.dumps(export_data, indent=2, ensure_ascii=False)

        return history, state_dict, export_json
    else:
        return [], {"status": "No saved state for this user"}, ""


def export_to_file(export_json: str, user_id: str) -> str | None:
    """
    Exports conversation to temporary JSON file.

    Args:
        export_json: JSON string with conversation data
        user_id: User ID (for filename)

    Returns:
        str: Path to temporary file
    """
    if not export_json or export_json == "":
        return None

    # Create temp file with meaningful name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"coach_conversation_{user_id}_{timestamp}.json"

    # Save to temp file
    temp_dir = Path(tempfile.gettempdir())
    filepath = temp_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(export_json)

    return str(filepath)


def evaluate_conversation(export_json: str, priority_filter: str, progress=gr.Progress()) -> str:
    """
    Evaluate conversation using LLM-as-Judge.

    Args:
        export_json: JSON string with conversation data
        priority_filter: "MUST-HAVE", "SHOULD-HAVE", or "ALL"
        progress: Gradio progress tracker

    Returns:
        Formatted evaluation results
    """
    progress(0, desc="Starting evaluation...")

    if not export_json or export_json == "":
        return "⚠️ **No conversation to evaluate.** Start a conversation first."

    # Parse export data
    progress(0.1, desc="Parsing conversation...")
    try:
        export_data = json.loads(export_json)
        conversation = export_data.get("state", {}).get("conversation_history", [])

        if not conversation:
            return "⚠️ **No messages in conversation.** Have a conversation with the coach first."

    except Exception as e:
        return f"❌ **Error parsing conversation:** {str(e)}"

    # Parse leaderboard card
    progress(0.2, desc="Loading evaluation criteria...")
    try:
        leaderboard_path = Path(__file__).parent / "leaderboard_card_coach.md"
        all_checks = parse_leaderboard_card(str(leaderboard_path))

        if not all_checks:
            return "❌ **Error:** No criteria found in leaderboard card."

    except Exception as e:
        return f"❌ **Error parsing leaderboard:** {str(e)}"

    # Filter checks by priority
    progress(0.3, desc=f"Filtering criteria ({priority_filter})...")
    filtered_checks = filter_checks_by_priority(all_checks, priority_filter)

    if not filtered_checks:
        return f"⚠️ **No criteria match filter:** {priority_filter}"

    # Evaluate using LLM
    progress(0.4, desc=f"Evaluating {len(filtered_checks)} criteria with LLM...")
    try:
        eval_result = evaluate_conv_llm(conversation, filtered_checks)

        if "error" in eval_result:
            return f"❌ **Evaluation error:** {eval_result['error']}"

        # Format results
        progress(0.9, desc="Formatting results...")
        formatted = format_evaluation_results(eval_result)

        progress(1.0, desc="Done!")
        return formatted

    except LifeCoachError as e:
        log.error("evaluation_failed", error=str(e))
        return f"❌ **Evaluation failed:** {str(e)}"
    except Exception as e:
        import traceback

        error_detail = traceback.format_exc()
        log.error("evaluation_unexpected", error=str(e))
        return f"❌ **Evaluation failed:**\n\n```\n{error_detail}\n```"


# ===================================================================
# Building Gradio interface
# ===================================================================

with gr.Blocks(title="Life Coach System", theme=gr.themes.Default()) as demo:
    gr.Markdown("# Life Coach System")
    gr.Markdown("**Features:** Multi-user • Memory State • Leaderboard Evaluation")

    with gr.Row():
        # ===============================================================
        # LEFT COLUMN: Chat Interface (70%)
        # ===============================================================
        with gr.Column(scale=7):
            chatbot = gr.Chatbot(type="messages", height=600, show_label=False)

            msg = gr.Textbox(placeholder="Message...", lines=2, show_label=False)

            with gr.Row():
                send_btn = gr.Button("Send", variant="primary", scale=3)
                clear_btn = gr.Button("Clear", variant="secondary", scale=1)

        # ===============================================================
        # RIGHT COLUMN: Sidebar (30%)
        # ===============================================================
        with gr.Column(scale=3, variant="panel"):
            gr.Markdown("### Controls")

            user_id_input = gr.Textbox(
                label="User ID",
                value=settings.default_user_id,
                placeholder="Enter your ID",
                info="Each user has independent state",
            )

            # Memory State (collapsed)
            with gr.Accordion("🧠 Memory State", open=False):
                state_viewer = gr.JSON(
                    label="Session State", value={"status": "No state - start conversation"}
                )

            # Export (collapsed)
            with gr.Accordion("⚙️ Advanced", open=False):
                gr.Markdown("**Export Session**")

                export_data = gr.Textbox(
                    label="Export data (JSON)",
                    lines=1,
                    visible=False,  # Hidden field for storing JSON
                )

                export_btn = gr.Button("📥 Export JSON", size="sm")

                export_file = gr.File(label="Download", visible=True)

            # Leaderboard (collapsed)
            with gr.Accordion("📊 Leaderboard", open=False):
                gr.Markdown("**Evaluate Conversation Quality**")

                priority_dropdown = gr.Dropdown(
                    choices=["ALL", "MUST-HAVE", "SHOULD-HAVE"],
                    value="MUST-HAVE",
                    label="Priority Filter",
                    info="Select which criteria to evaluate",
                    interactive=True,
                )

                evaluate_btn = gr.Button("🎯 Evaluate", variant="primary", size="sm")

                leaderboard_results = gr.Markdown(value="*Click 'Evaluate' to see results...*")

    # ===================================================================
    # Event handlers
    # ===================================================================

    # Send message (button)
    send_btn.click(
        fn=interact,
        inputs=[msg, chatbot, user_id_input],
        outputs=[chatbot, state_viewer, export_data],
    ).then(
        lambda: "",  # Clear text field after sending
        None,
        msg,
    )

    # Send message (Enter)
    msg.submit(
        fn=interact,
        inputs=[msg, chatbot, user_id_input],
        outputs=[chatbot, state_viewer, export_data],
    ).then(
        lambda: "",  # Clear text field
        None,
        msg,
    )

    # Reset conversation
    clear_btn.click(
        fn=reset_conversation, inputs=[user_id_input], outputs=[chatbot, state_viewer, export_data]
    )

    # Export conversation to file
    export_btn.click(fn=export_to_file, inputs=[export_data, user_id_input], outputs=[export_file])

    # Evaluate conversation
    evaluate_btn.click(
        fn=evaluate_conversation,
        inputs=[export_data, priority_dropdown],
        outputs=[leaderboard_results],
        show_progress="full",  # Show progress bar and disable button during execution
    )


def main() -> None:
    """Entry point for the Life Coach System dev UI."""
    configure_logging()
    log.info(
        "startup",
        model=settings.model_name,
        coach_name=settings.coach_name,
        storage=settings.persistence_backend,
        debug=settings.debug,
    )
    demo.launch(
        server_name="0.0.0.0",
        server_port=8080,
        share=False,  # Set True if you want public link
    )


# ===================================================================
# Launch application
# ===================================================================

if __name__ == "__main__":
    main()
