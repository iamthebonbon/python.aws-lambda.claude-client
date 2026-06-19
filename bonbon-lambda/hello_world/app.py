import json
import os

import anthropic

MODEL = "claude-haiku-4-5-20251001"


def lambda_handler(event, context):
    params = event.get("queryStringParameters") or {}
    prompt = params.get("prompt", "Say hello!")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    message = response.content[0].text

    return {
        "statusCode": 200,
        "body": json.dumps({"message": message}),
    }
