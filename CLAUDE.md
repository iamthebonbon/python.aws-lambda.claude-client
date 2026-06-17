# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python AWS Lambda function exposed via API Gateway, built with AWS SAM. Deployed stack name: `bonbon-lambda`. Runtime: Python 3.14, architecture: x86_64.

All SAM commands must be run from inside the `bonbon-lambda/` directory.

## Commands

```bash
cd bonbon-lambda

# Build
sam build

# Run locally (API on port 3000)
sam local start-api

# Invoke function directly
sam local invoke HelloWorldFunction --event events/event.json

# Unit tests
pip install -r tests/requirements.txt --user
python -m pytest tests/unit -v

# Integration tests (requires deployed stack)
AWS_SAM_STACK_NAME="bonbon-lambda" python -m pytest tests/integration -v

# Deploy (first time)
sam deploy --guided

# Deploy (subsequent)
sam deploy

# Tear down
sam delete --stack-name "bonbon-lambda"
```

## Architecture

```
bonbon-lambda/
  hello_world/app.py      # Lambda handler: lambda_handler(event, context)
  template.yaml           # SAM/CloudFormation template (function + implicit API Gateway)
  samconfig.toml          # SAM CLI defaults (stack name, S3, capabilities)
  events/event.json       # Sample API Gateway proxy event for local invocation
  tests/unit/             # Pytest unit tests (no AWS needed)
  tests/integration/      # Pytest integration tests (hit deployed API Gateway)
```

The handler returns API Gateway Lambda Proxy format. SAM wires `GET /hello` → `HelloWorldFunction`. Global timeout is 3 seconds, logging is JSON.

Integration tests resolve the live API URL from CloudFormation stack outputs via `AWS_SAM_STACK_NAME`.

When adding new Lambda functions, add them as additional `AWS::Serverless::Function` resources in `template.yaml` — each gets its own isolated build artifact under `.aws-sam/build/<FunctionName>/`.

## Instructions
- Keep operational, cost and memory efficiency
- Don't propose complexity
- Be extremely concise
