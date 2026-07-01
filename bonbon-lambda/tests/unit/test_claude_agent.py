import json
from unittest.mock import MagicMock, patch

import pytest

from hello_world import app


def _make_text_block(text):
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _make_tool_use_block(tool_id, name, input_data):
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_id
    block.name = name
    block.input = input_data
    return block


def _make_response(content, stop_reason):
    resp = MagicMock()
    resp.content = content
    resp.stop_reason = stop_reason
    return resp


def test_run_agent_calls_tool_and_returns_answer():
    tool_block = _make_tool_use_block("tool-1", "get_current_time", {})
    final_text_block = _make_text_block("The current time is 2026-06-19T07:00:00+00:00.")

    first_response = _make_response([tool_block], "tool_use")
    second_response = _make_response([final_text_block], "end_turn")

    client = MagicMock()
    client.messages.create.side_effect = [first_response, second_response]

    result = app.run_agent(client, "What time is it?")

    assert result["answer"] == "The current time is 2026-06-19T07:00:00+00:00."
    trace = result["trace"]
    phases = [t["phase"] for t in trace]
    assert phases == ["ACT", "OBSERVE", "THINK"]
    assert trace[0]["tool"] == "get_current_time"
    assert trace[1]["tool"] == "get_current_time"
    assert "result" in trace[1]


def test_run_agent_think_before_tool():
    think_block = _make_text_block("I need to check the time.")
    tool_block = _make_tool_use_block("tool-2", "get_current_time", {})
    final_text_block = _make_text_block("Done.")

    first_response = _make_response([think_block, tool_block], "tool_use")
    second_response = _make_response([final_text_block], "end_turn")

    client = MagicMock()
    client.messages.create.side_effect = [first_response, second_response]

    result = app.run_agent(client, "What time is it?")

    phases = [t["phase"] for t in result["trace"]]
    assert phases[0] == "THINK"
    assert "ACT" in phases
    assert "OBSERVE" in phases


def test_run_agent_returns_json_serializable_messages():
    tool_block = _make_tool_use_block("tool-1", "get_current_time", {})
    final_text_block = _make_text_block("It is now.")

    first_response = _make_response([tool_block], "tool_use")
    second_response = _make_response([final_text_block], "end_turn")

    client = MagicMock()
    client.messages.create.side_effect = [first_response, second_response]

    result = app.run_agent(client, "What time is it?")

    # Must round-trip through JSON so it can be returned and resent as-is.
    messages = json.loads(json.dumps(result["messages"]))
    assert messages[0] == {"role": "user", "content": "What time is it?"}
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"][0] == {
        "type": "tool_use",
        "id": "tool-1",
        "name": "get_current_time",
        "input": {},
    }
    assert messages[2]["role"] == "user"
    assert messages[2]["content"][0]["type"] == "tool_result"
    assert messages[3] == {
        "role": "assistant",
        "content": [{"type": "text", "text": "It is now."}],
    }


def test_run_agent_continues_conversation_from_history():
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": [{"type": "text", "text": "Hello!"}]},
    ]
    final_text_block = _make_text_block("It is now.")
    response = _make_response([final_text_block], "end_turn")

    client = MagicMock()
    client.messages.create.return_value = response

    result = app.run_agent(client, "What time is it?", history)

    assert result["messages"][:2] == history
    assert result["messages"][2] == {"role": "user", "content": "What time is it?"}
    sent_messages = client.messages.create.call_args.kwargs["messages"]
    assert sent_messages[:2] == history


def test_lambda_handler_returns_200():
    event = {"body": json.dumps({"prompt": "What time is it?"})}

    final_text_block = _make_text_block("It is now.")
    response = _make_response([final_text_block], "end_turn")

    mock_client = MagicMock()
    mock_client.messages.create.return_value = response

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("hello_world.app.anthropic.Anthropic", return_value=mock_client):
            ret = app.lambda_handler(event, "")

    assert ret["statusCode"] == 200
    body = json.loads(ret["body"])
    assert body["answer"] == "It is now."
    assert body["messages"][-1]["content"][0]["text"] == "It is now."


def test_lambda_handler_resends_messages_to_continue_conversation():
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": [{"type": "text", "text": "Hello!"}]},
    ]
    event = {
        "body": json.dumps({"prompt": "What time is it?", "messages": history})
    }

    final_text_block = _make_text_block("It is now.")
    response = _make_response([final_text_block], "end_turn")

    mock_client = MagicMock()
    mock_client.messages.create.return_value = response

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("hello_world.app.anthropic.Anthropic", return_value=mock_client):
            ret = app.lambda_handler(event, "")

    assert ret["statusCode"] == 200
    sent_messages = mock_client.messages.create.call_args.kwargs["messages"]
    assert sent_messages[:2] == history


def test_lambda_handler_missing_prompt_returns_400():
    for event in [{"body": None}, {"body": json.dumps({})}]:
        ret = app.lambda_handler(event, "")
        assert ret["statusCode"] == 400
        body = json.loads(ret["body"])
        assert "error" in body


def test_lambda_handler_invalid_messages_type_returns_400():
    event = {"body": json.dumps({"prompt": "Hi", "messages": "not-a-list"})}

    ret = app.lambda_handler(event, "")

    assert ret["statusCode"] == 400
    body = json.loads(ret["body"])
    assert "error" in body
