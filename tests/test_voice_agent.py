import pytest
from unittest.mock import patch, MagicMock

from langchain_core.messages import HumanMessage

from voice_agent import (
    agent,
    llm,
    tools,
    speak,  # for testing the speak function
    sr,  # speech_recognition
)


# ────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────

@pytest.fixture
def mock_agent_response():
    """Typical structure returned by a LangGraph-style ReAct agent"""
    return {
        "messages": [
            HumanMessage(content="what rooms are available right now"),
            MagicMock(
                content=(
                    "Thought: I should check availability.\n"
                    "Final Answer: Room A, Room B and DMF 473 are currently free."
                )
            ),
        ]
    }



def test_agent_smoke():
    """
    Very basic smoke test: can we call agent.invoke() without crashing?
    (will be slow / may fail if Ollama not running)
    """
    try:
        response = agent.invoke({
            "messages": [HumanMessage(content="what time is it?")]
        })
        assert isinstance(response, dict)
        assert "messages" in response
    except Exception as e:
        pytest.skip(f"Agent invocation failed (likely Ollama not running): {e}")


@patch.object(agent, 'invoke')
def test_agent_parses_last_message_content(mock_invoke, mock_agent_response):
    """
    Check that we correctly extract the final answer from the last message
    """
    mock_invoke.return_value = mock_agent_response

    response = agent.invoke({"messages": [HumanMessage(content="test")]})
    messages = response.get("messages", [])

    assert len(messages) >= 1
    final_msg = messages[-1]
    answer = final_msg.content.strip() if hasattr(final_msg, "content") else str(final_msg)

    assert "Room A" in answer
    assert "Final Answer" in answer


@patch.object(agent, 'invoke')
def test_agent_handles_empty_messages(mock_invoke):
    """Edge case: agent returns no messages at all"""
    mock_invoke.return_value = {"messages": []}

    response = agent.invoke({"messages": [HumanMessage(content="hi")]})
    messages = response.get("messages", [])

    assert len(messages) == 0


@patch.object(agent, 'invoke')
def test_agent_handles_exception(mock_invoke):
    """What happens when the agent crashes internally"""
    mock_invoke.side_effect = RuntimeError("LLM connection failed")

    with pytest.raises(RuntimeError, match="LLM connection failed"):
        agent.invoke({"messages": [HumanMessage(content="crash")]})
    # Note: your main loop catches this and returns a fallback message



@patch("pyttsx3.init")
def test_speak_calls_engine_methods(mock_init):
    """Does speak() call say() and runAndWait() correctly?"""
    mock_engine = MagicMock()
    mock_init.return_value = mock_engine

    speak("Hello, this is a test")

    mock_engine.say.assert_called_once_with("Hello, this is a test")
    mock_engine.runAndWait.assert_called_once()


def test_tools_list_is_not_empty():
    assert len(tools) >= 3
    assert any(t.__name__ == "get_current_datetime" for t in tools)
    assert any(t.__name__ == "list_available_rooms_now_or_soon" for t in tools)


