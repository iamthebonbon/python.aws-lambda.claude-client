import json
from unittest.mock import MagicMock, patch

import pytest

from hello_world import app


def _make_text_block(text):
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _make_response(content):
    resp = MagicMock()
    resp.content = content
    return resp


def test_lambda_handler_with_prompt():
    event = {"queryStringParameters": {"prompt": "Say hi!"}}

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response([_make_text_block("Hi there!")])

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("hello_world.app.anthropic.Anthropic", return_value=mock_client):
            ret = app.lambda_handler(event, "")

    assert ret["statusCode"] == 200
    body = json.loads(ret["body"])
    assert body["message"] == "Hi there!"
    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["messages"][0]["content"] == "Say hi!"


def test_lambda_handler_default_prompt():
    event = {"queryStringParameters": None}

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response([_make_text_block("Hello!")])

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("hello_world.app.anthropic.Anthropic", return_value=mock_client):
            ret = app.lambda_handler(event, "")

    assert ret["statusCode"] == 200
    body = json.loads(ret["body"])
    assert "message" in body
    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["messages"][0]["content"] == "Say hello!"
