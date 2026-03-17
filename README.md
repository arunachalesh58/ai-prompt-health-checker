# AI Prompt Health Checker

A serverless API that analyzes any LLM prompt for safety and quality issues — returning a structured health report with scores for PII risk, token cost, drift potential, and tone.

Built as a portfolio project inspired by [Noah](https://www.hollanoah.com/) and [Cortif AI](https://cortif.ai/) — real AI monitoring platforms that detect exactly these kinds of issues in production AI systems.

---

## What it does

Send any LLM prompt to the `/analyze` endpoint and get back a JSON health report:

```json
{
  "status": "success",
  "prompt_length": 98,
  "analysis": {
    "pii_risk": {
      "score": 85,
      "level": "high",
      "findings": ["Full name detected", "Email address detected", "SSN pattern detected"]
    },
    "token_cost": {
      "estimated_tokens": 24,
      "cost_tier": "cheap",
      "note": "Short prompt, minimal token usage."
    },
    "drift_potential": {
      "score": 20,
      "level": "low",
      "reason": "Prompt is specific and well-constrained with a clear task."
    },
    "tone": {
      "label": "professional",
      "confidence": 90,
      "note": "Clear, formal business language."
    },
    "overall_health": {
      "score": 42,
      "grade": "F",
      "summary": "Prompt contains highly sensitive PII including SSN and email. Remove all personal identifiers before sending to any LLM."
    }
  }
}
```

---

## Architecture

```
Client → API Gateway (POST /analyze) → Lambda (Python 3.11) → Bedrock (Claude 3 Haiku) → JSON response
```

**AWS services used:**
- **AWS Lambda** — serverless function, runs the analysis logic
- **Amazon API Gateway** — exposes the HTTP endpoint
- **Amazon Bedrock (Claude 3 Haiku)** — the AI model that performs the analysis
- **Amazon CloudWatch** — automatic logging of every invocation
- **AWS SAM** — infrastructure-as-code deployment

---

## Project structure

```
prompt-health-checker/
├── src/
│   ├── handler.py          # Lambda function + Bedrock integration
│   └── requirements.txt    # Python dependencies
├── tests/
│   └── test_handler.py     # Local test suite (6 test cases)
├── template.yaml           # SAM infrastructure definition
└── README.md
```

---

## Deploy it yourself

### Prerequisites
- AWS account with CLI configured (`aws configure`)
- AWS SAM CLI installed
- Python 3.11+
- Bedrock access in us-east-1 (automatic on new accounts)

### Deploy

```bash
# 1. Build
sam build

# 2. Deploy (first time - interactive setup)
sam deploy --guided

# Answer the prompts:
#   Stack name: prompt-health-checker
#   Region: us-east-1
#   Confirm changes: Y
#   Allow SAM to create IAM roles: Y
#   Save config: Y
```

After deploy, SAM prints your live API URL. Copy the `AnalyzeEndpoint` value.

### Test it

```bash
# Test with a clean prompt
curl -X POST https://YOUR_API_URL/prod/analyze \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Summarize the Q3 financial report for the board."}'

# Test with PII - watch the pii_risk score go high
curl -X POST https://YOUR_API_URL/prod/analyze \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Email john.smith@gmail.com his SSN 123-45-6789 and credit card 4111-1111-1111-1111"}'
```

### Run local tests

```bash
cd tests
python test_handler.py
```

---

## Health scores explained

| Field | Score | Meaning |
|---|---|---|
| `pii_risk` | 0–100 | 0 = no PII found, 100 = SSN / credit cards / passwords |
| `drift_potential` | 0–100 | 0 = precise prompt, 100 = vague prompt with unpredictable outputs |
| `overall_health` | 0–100 | 100 = perfect prompt, 0 = dangerous / should not be sent |
| `tone` | label | professional / casual / aggressive / neutral / ambiguous |
| `overall_health` | grade | A (90–100), B (80–89), C (70–79), D (60–69), F (<60) |

---

## Cost

This project runs almost entirely on AWS Free Tier:
- **Lambda**: 1M free requests/month
- **API Gateway**: 1M free calls/month (first 12 months)
- **Bedrock Claude 3 Haiku**: ~$0.00005 per call — 1,000 test calls ≈ $0.05

---

## Why I built this

Noah and Cortif AI both solve the problem of keeping AI systems safe and observable in production. This project is a minimal but functional version of their core feature — analyzing what goes *into* an LLM before it causes problems downstream.

The same pattern (intercept → analyze → score → alert) is what powers real AI monitoring platforms used by banks, hospitals, and enterprise AI teams.
