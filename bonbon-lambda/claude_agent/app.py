import json
import datetime
import os

import anthropic

MODEL = "claude-sonnet-4-6"

TOOLS = [
    {
        "name": "get_current_time",
        "description": "Returns the current UTC date and time in ISO 8601 format.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    }
]


def get_current_time() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def run_agent(client: anthropic.Anthropic, prompt: str) -> dict:
    messages = [{"role": "user", "content": prompt}]
    trace = []

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        # THINK: capture any text reasoning before acting
        for block in response.content:
            if block.type == "text":
                trace.append({"phase": "THINK", "content": block.text})

        if response.stop_reason == "end_turn":
            final = next((b.text for b in response.content if b.type == "text"), "")
            return {"answer": final, "trace": trace}

        # ACT: execute each tool the model requested
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            trace.append({"phase": "ACT", "tool": block.name, "input": block.input})

            if block.name == "get_current_time":
                result = get_current_time()
            else:
                result = f"Unknown tool: {block.name}"

            # OBSERVE: record what the tool returned
            trace.append({"phase": "OBSERVE", "tool": block.name, "result": result})
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": result}
            )

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")
    prompt = body.get("prompt", "").strip()

    if not prompt:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "prompt is required"}),
        }

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = run_agent(client, prompt)

    return {
        "statusCode": 200,
        "body": json.dumps(result),
    }
