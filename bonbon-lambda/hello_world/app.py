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
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    answer = next((b.text for b in response.content if b.type == "text"), "")

    return {
        "statusCode": 200,
        "body": json.dumps({"message": answer}),
    }
