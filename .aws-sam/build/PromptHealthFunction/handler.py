import json
import boto3
import re
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

MODEL_ID = "amazon.nova-lite-v1:0"

SYSTEM_PROMPT = """You are an AI prompt safety and quality analyzer.
When given a prompt, analyze it and return ONLY a valid JSON object with exactly these fields, no explanation, no markdown, no code fences:

{
  "pii_risk": {
    "score": <integer 0-100>,
    "level": "<none|low|medium|high>",
    "findings": [<list of strings describing PII found, empty list if none>]
  },
  "token_cost": {
    "estimated_tokens": <integer>,
    "cost_tier": "<cheap|moderate|expensive>",
    "note": "<one short sentence>"
  },
  "drift_potential": {
    "score": <integer 0-100>,
    "level": "<low|medium|high>",
    "reason": "<one short sentence>"
  },
  "tone": {
    "label": "<professional|casual|aggressive|neutral|ambiguous>",
    "confidence": <integer 0-100>,
    "note": "<one short sentence>"
  },
  "overall_health": {
    "score": <integer 0-100>,
    "grade": "<A|B|C|D|F>",
    "summary": "<two sentences max>"
  }
}

Scoring guide:
- pii_risk score: 0=no PII, 100=highly sensitive PII (SSN, credit card, passwords)
- drift_potential score: 0=very focused prompt, 100=vague prompt with inconsistent outputs
- overall_health score: 100=perfect prompt, 0=dangerous prompt
- estimated_tokens: roughly 1 token per 4 characters
Return ONLY the raw JSON. Nothing else."""


def analyze_prompt(prompt_text: str) -> dict:
    body = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [{"text": f"Analyze this prompt:\n\n{prompt_text}"}]
            }
        ],
        "system": [{"text": SYSTEM_PROMPT}],
        "inferenceConfig": {
            "maxTokens": 1024,
            "temperature": 0.1
        }
    })

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body
    )

    response_body = json.loads(response["body"].read())
    raw_text = response_body["output"]["message"]["content"][0]["text"].strip()

    raw_text = re.sub(r"^```json\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)

    start = raw_text.find("{")
    end = raw_text.rfind("}") + 1
    if start != -1 and end > start:
        raw_text = raw_text[start:end]

    return json.loads(raw_text)


def build_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, indent=2)
    }


def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    if event.get("httpMethod") == "OPTIONS":
        return build_response(200, {"message": "ok"})

    if event.get("httpMethod") != "POST":
        return build_response(405, {"error": "Method not allowed. Use POST."})

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return build_response(400, {"error": "Invalid JSON in request body."})

    prompt_text = body.get("prompt", "").strip()

    if not prompt_text:
        return build_response(400, {
            "error": "Missing required field: 'prompt'",
            "example": {"prompt": "Summarize the quarterly report for the board"}
        })

    if len(prompt_text) > 10000:
        return build_response(400, {"error": "Prompt too long. Maximum 10,000 characters."})

    try:
        logger.info("Analyzing prompt of length: %d characters", len(prompt_text))
        analysis = analyze_prompt(prompt_text)

        result = {
            "status": "success",
            "prompt_length": len(prompt_text),
            "model_used": MODEL_ID,
            "analysis": analysis
        }

        logger.info("Analysis complete. Overall health score: %s",
                    analysis.get("overall_health", {}).get("score", "unknown"))

        return build_response(200, result)

    except json.JSONDecodeError as e:
        logger.error("Failed to parse response as JSON: %s", str(e))
        return build_response(500, {"error": "Model returned unparseable response.", "detail": str(e)})

    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        return build_response(500, {"error": "Internal server error.", "detail": str(e)})