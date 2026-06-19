import json
from unittest.mock import MagicMock, patch

import pytest

from hello_world import app


@pytest.fixture()
def apigw_event():
    return {
        "queryStringParameters": {"prompt": "Tell me a joke"},
        "httpMethod": "GET",
        "path": "/hello",
    }


@pytest.fixture()
def apigw_event_no_prompt():
    return {
        "queryStringParameters": None,
        "httpMethod": "GET",
        "path": "/hello",
    }


def _mock_client(reply: str):
    content_block = MagicMock()
    content_block.text = reply
    response = MagicMock()
    response.content = [content_block]
    client = MagicMock()
    client.messages.create.return_value = response
    return client


def test_lambda_handler_with_prompt(apigw_event):
    mock_client = _mock_client("Why did the chicken cross the road?")
    with patch("hello_world.app.anthropic.Anthropic", return_value=mock_client):
        ret = app.lambda_handler(apigw_event, "")

    assert ret["statusCode"] == 200
    data = json.loads(ret["body"])
    assert data["message"] == "Why did the chicken cross the road?"
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["messages"][0]["content"] == "Tell me a joke"


def test_lambda_handler_default_prompt(apigw_event_no_prompt):
    mock_client = _mock_client("Hello!")
    with patch("hello_world.app.anthropic.Anthropic", return_value=mock_client):
        ret = app.lambda_handler(apigw_event_no_prompt, "")

    assert ret["statusCode"] == 200
    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["messages"][0]["content"] == "Say hello!"
