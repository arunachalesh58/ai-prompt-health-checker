"""
Local tests for the prompt health checker Lambda.
Run with: python tests/test_handler.py

These tests call Bedrock directly so you need AWS credentials configured.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from handler import lambda_handler


def make_event(prompt: str, method: str = "POST") -> dict:
    """Simulate an API Gateway event."""
    return {
        "httpMethod": method,
        "body": json.dumps({"prompt": prompt}),
        "headers": {"Content-Type": "application/json"}
    }


def print_result(test_name: str, response: dict):
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"Status: {response['statusCode']}")
    body = json.loads(response["body"])
    print(json.dumps(body, indent=2))


def test_clean_prompt():
    """A clean professional prompt - should score high health."""
    event = make_event(
        "Summarize the key findings from the Q3 2024 financial report "
        "and highlight any areas of concern for the board."
    )
    response = lambda_handler(event, {})
    print_result("Clean professional prompt", response)
    assert response["statusCode"] == 200


def test_pii_prompt():
    """Prompt containing PII - should flag high PII risk."""
    event = make_event(
        "Write an email to John Smith at john.smith@gmail.com. "
        "His phone is 555-123-4567 and his SSN is 123-45-6789. "
        "His credit card number is 4111-1111-1111-1111."
    )
    response = lambda_handler(event, {})
    print_result("Prompt with PII (name, email, SSN, credit card)", response)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    pii_score = body["analysis"]["pii_risk"]["score"]
    print(f"\n  PII score: {pii_score}/100 (expected: high, 70+)")


def test_vague_prompt():
    """Very vague prompt - should flag high drift potential."""
    event = make_event("Do something good.")
    response = lambda_handler(event, {})
    print_result("Vague prompt (drift risk)", response)
    assert response["statusCode"] == 200


def test_missing_prompt():
    """No prompt field - should return 400 error."""
    event = {
        "httpMethod": "POST",
        "body": json.dumps({"text": "wrong field name"}),
        "headers": {}
    }
    response = lambda_handler(event, {})
    print_result("Missing prompt field (expect 400)", response)
    assert response["statusCode"] == 400


def test_wrong_method():
    """GET request - should return 405."""
    event = make_event("anything", method="GET")
    response = lambda_handler(event, {})
    print_result("Wrong HTTP method GET (expect 405)", response)
    assert response["statusCode"] == 405


def test_empty_prompt():
    """Empty string - should return 400."""
    event = make_event("")
    response = lambda_handler(event, {})
    print_result("Empty prompt (expect 400)", response)
    assert response["statusCode"] == 400


if __name__ == "__main__":
    print("Running Prompt Health Checker tests...")
    print("These calls go to real Bedrock - expect ~2-3 seconds per test\n")

    tests = [
        test_clean_prompt,
        test_pii_prompt,
        test_vague_prompt,
        test_missing_prompt,
        test_wrong_method,
        test_empty_prompt,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAILED: {test.__name__} - {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__} - {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
