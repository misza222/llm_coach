
# -*- coding: utf-8 -*-
"""
Gradio UI for Life Coach System.

This file contains the complete user interface for the coaching system.
Run: python app.py
"""

import gradio as gr
import json
import tempfile
from datetime import datetime
from pathlib import Path
from engine.coach import CoachAgent
from persistence.in_memory import InMemoryBackend
from memory.logic.manager import MemoryManager
from memory.schemas.session_state import SessionState
from config import Config
from utils.leaderboard_parser import parse_leaderboard_card, filter_checks_by_priority
from utils.evaluator import evaluate_conversation as evaluate_conv_llm, format_evaluation_results

# ===================================================================
# Global instances (singleton pattern)
# ===================================================================

coach = CoachAgent()
storage = InMemoryBackend()
memory_manager = MemoryManager()


# ===================================================================
# UI handling functions
# ===================================================================

def interact(message: str, history: list, user_id: str):
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
        user_id = Config.DEFAULT_USER_ID

    # Get or create state
    if storage.exists(user_id):
        state_dict = storage.load(user_id)
        state = SessionState(**state_dict)
    else:
        state = memory_manager.create_empty_state(user_id)

    # Generate coach response
    try:
        response_text, updated_state = coach.respond(message, state)
    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        print(f"ERROR: {error_msg}")
        return history, {"error": error_msg}, ""

    # Save state
    storage.save(user_id, updated_state.model_dump())

    # Update Gradio history (messages format: list of dicts)
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response_text})

    # Prepare state visualization (dict for gr.JSON)
    state_dict = updated_state.model_dump()

    # Prepare export data (convert history to tuples for export)
    export_history = []
    for i in range(0, len(history) - 1, 2):
        if i + 1 < len(history):
            export_history.append((
                history[i].get("content", ""),
                history[i + 1].get("content", "")
            ))

    export_data = {
        "user_id": user_id,
        "exported_at": datetime.now().isoformat(),
        "conversation": export_history,
        "state": updated_state.model_dump()
    }
    export_json = json.dumps(export_data, indent=2, ensure_ascii=False)

    return history, state_dict, export_json


def reset_conversation(user_id: str):
    """
    Resets conversation (clears history and state).

    Args:
        user_id: User ID

    Returns:
        Tuple: (empty_history, message, empty_export)
    """
    if not user_id or not user_id.strip():
        user_id = Config.DEFAULT_USER_ID

    if storage.exists(user_id):
        storage.delete(user_id)

    return [], {"status": "State cleared"}, ""


def load_state_for_user(user_id: str):
    """
    Loads state for given user (to display when user_id changes).

    Args:
        user_id: User ID

    Returns:
        Tuple: (history, state_dict, export_json)
    """
    if not user_id or not user_id.strip():
        user_id = Config.DEFAULT_USER_ID

    if storage.exists(user_id):
        state_dict = storage.load(user_id)
        state = SessionState(**state_dict)

        # Reconstruct history for Gradio messages format (list of dicts)
        history = []
        for msg in state.conversation_history:
            history.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        state_dict = state.model_dump()

        # Convert history to tuples for export
        export_history = []
        for i in range(0, len(history) - 1, 2):
            if i + 1 < len(history):
                export_history.append((
                    history[i].get("content", ""),
                    history[i + 1].get("content", "")
                ))

        export_data = {
            "user_id": user_id,
            "exported_at": datetime.now().isoformat(),
            "conversation": export_history,
            "state": state.model_dump()
        }
        export_json = json.dumps(export_data, indent=2, ensure_ascii=False)

        return history, state_dict, export_json
    else:
        return [], {"status": "No saved state for this user"}, ""


def export_to_file(export_json: str, user_id: str) -> str:
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

    with open(filepath, 'w', encoding='utf-8') as f:
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

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return f"❌ **Evaluation failed:**\n\n```\n{error_detail}\n```"


# ===================================================================
# Building Gradio interface
# ===================================================================

with gr.Blocks(
    title="Life Coach System",
    theme=gr.themes.Default()
) as demo:
    gr.Markdown("# Life Coach System")
    gr.Markdown("**Features:** Multi-user • Memory State • Leaderboard Evaluation")

    with gr.Row():
        # ===============================================================
        # LEFT COLUMN: Chat Interface (70%)
        # ===============================================================
        with gr.Column(scale=7):
            chatbot = gr.Chatbot(
                type="messages",
                height=600,
                show_label=False
            )

            msg = gr.Textbox(
                placeholder="Message...",
                lines=2,
                show_label=False
            )

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
                value=Config.DEFAULT_USER_ID,
                placeholder="Enter your ID",
                info="Each user has independent state"
            )

            # Memory State (collapsed)
            with gr.Accordion("🧠 Memory State", open=False):
                state_viewer = gr.JSON(
                    label="Session State",
                    value={"status": "No state - start conversation"}
                )

            # Export (collapsed)
            with gr.Accordion("⚙️ Advanced", open=False):
                gr.Markdown("**Export Session**")

                export_data = gr.Textbox(
                    label="Export data (JSON)",
                    lines=1,
                    visible=False  # Hidden field for storing JSON
                )

                export_btn = gr.Button("📥 Export JSON", size="sm")

                export_file = gr.File(
                    label="Download",
                    visible=True
                )

            # Leaderboard (collapsed) - NEW
            with gr.Accordion("📊 Leaderboard", open=False):
                gr.Markdown("**Evaluate Conversation Quality**")

                priority_dropdown = gr.Dropdown(
                    choices=["ALL", "MUST-HAVE", "SHOULD-HAVE"],
                    value="MUST-HAVE",
                    label="Priority Filter",
                    info="Select which criteria to evaluate",
                    interactive=True
                )

                evaluate_btn = gr.Button("🎯 Evaluate", variant="primary", size="sm")

                leaderboard_results = gr.Markdown(
                    value="*Click 'Evaluate' to see results...*"
                )


    # ===================================================================
    # Event handlers
    # ===================================================================

    # Send message (button)
    send_btn.click(
        fn=interact,
        inputs=[msg, chatbot, user_id_input],
        outputs=[chatbot, state_viewer, export_data]
    ).then(
        lambda: "",  # Clear text field after sending
        None,
        msg
    )

    # Send message (Enter)
    msg.submit(
        fn=interact,
        inputs=[msg, chatbot, user_id_input],
        outputs=[chatbot, state_viewer, export_data]
    ).then(
        lambda: "",  # Clear text field
        None,
        msg
    )

    # Reset conversation
    clear_btn.click(
        fn=reset_conversation,
        inputs=[user_id_input],
        outputs=[chatbot, state_viewer, export_data]
    )

    # Export conversation to file
    export_btn.click(
        fn=export_to_file,
        inputs=[export_data, user_id_input],
        outputs=[export_file]
    )

    # Evaluate conversation
    evaluate_btn.click(
        fn=evaluate_conversation,
        inputs=[export_data, priority_dropdown],
        outputs=[leaderboard_results],
        show_progress="full"  # Show progress bar and disable button during execution
    )


# ===================================================================
# Launch application
# ===================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Life Coach System - MVP")
    print("=" * 70)
    print(f"Model: {Config.MODEL_NAME}")
    print(f"Coach Name: {Config.COACH_NAME}")
    print(f"Storage: {Config.PERSISTENCE_BACKEND}")
    print(f"Debug Mode: {Config.DEBUG}")
    print("=" * 70)

    demo.launch(
        server_name="0.0.0.0",
        server_port=8080,
        share=False  # Set True if you want public link
    )

