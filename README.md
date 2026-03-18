# AI Prompt Health Checker

A serverless API that analyzes any LLM prompt for safety and quality issues — returning a structured health report with scores for PII risk, token cost, drift potential, and tone.



---

## Live demo

**API endpoint (live on AWS):**

```
POST https://65o4g3sfo5.execute-api.us-east-1.amazonaws.com/prod/analyze
```

**Try it now (Windows PowerShell):**

```powershell
Invoke-WebRequest -Uri "https://65o4g3sfo5.execute-api.us-east-1.amazonaws.com/prod/analyze" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"prompt": "Summarize the Q3 financial report for the board."}' -UseBasicParsing | Select-Object -ExpandProperty Content
```

---

## What it does

Send any LLM prompt to the `/analyze` endpoint and get back a JSON health report:

```json
{
  "status": "success",
  "prompt_length": 82,
  "model_used": "amazon.nova-lite-v1:0",
  "analysis": {
    "pii_risk": {
      "score": 100,
      "level": "high",
      "findings": ["email address", "SSN", "credit card"]
    },
    "token_cost": {
      "estimated_tokens": 32,
      "cost_tier": "moderate",
      "note": "The prompt is moderately long."
    },
    "drift_potential": {
      "score": 10,
      "level": "low",
      "reason": "The prompt is very specific."
    },
    "tone": {
      "label": "neutral",
      "confidence": 90,
      "note": "The prompt is factual and neutral."
    },
    "overall_health": {
      "score": 10,
      "grade": "F",
      "summary": "The prompt contains highly sensitive PII and is unsafe. Avoid using such prompts."
    }
  }
}
```

---

## Architecture

```
Client → API Gateway (POST /analyze) → Lambda (Python 3.12) → Bedrock (Amazon Nova Lite) → JSON response
```

**AWS services used:**
- **AWS Lambda** — serverless function, runs the analysis logic
- **Amazon API Gateway** — exposes the HTTPS endpoint
- **Amazon Bedrock (Nova Lite)** — the AI model that performs the analysis
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
- Python 3.12+

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

### Test it (Windows PowerShell)

```powershell
# Clean prompt - should score Grade A
Invoke-WebRequest -Uri "https://YOUR_API_URL/analyze" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"prompt": "Summarize the Q3 financial report for the board."}' -UseBasicParsing | Select-Object -ExpandProperty Content

# PII prompt - watch pii_risk score hit 100
Invoke-WebRequest -Uri "https://YOUR_API_URL/analyze" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"prompt": "Email john.smith@gmail.com his SSN 123-45-6789 and credit card 4111-1111-1111-1111"}' -UseBasicParsing | Select-Object -ExpandProperty Content
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
- **Lambda** — 1M free requests/month
- **API Gateway** — 1M free calls/month (first 12 months)
- **Bedrock Nova Lite** — ~$0.000060 per 1,000 input tokens — 1,000 test calls ≈ $0.01

---

## Why I built this

This project is a minimal but functional version of their core feature — analyzing what goes into an LLM before it causes problems downstream.

The same pattern (intercept → analyze → score → alert) is what powers real AI monitoring platforms used by banks, hospitals, and enterprise AI teams.
