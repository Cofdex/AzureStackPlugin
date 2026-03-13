---
name: azure-foundry-evaluations
description: >
  Azure AI Evaluation SDK for Python (azure-ai-evaluation). Use for evaluating LLM
  outputs with built-in quality, safety, and NLP evaluators, and for running batch
  evaluations against datasets or target functions. Triggers on: "azure ai evaluation",
  "evaluate()", "GroundednessEvaluator", "RelevanceEvaluator", "ContentSafetyEvaluator",
  "azure-ai-evaluation", "LLM evaluation", "AI Foundry evals", "evaluator".
  CRITICAL: model_config is a dict, not ModelConfiguration class.
  column_mapping uses ${data.field} or ${outputs.field} syntax.
---

# Azure AI Evaluation SDK for Python

## Package
```bash
pip install azure-ai-evaluation
```

## Configuration

```python
# Required for AI-assisted evaluators (GroundednessEvaluator, etc.)
model_config = {
    "azure_endpoint": "https://myresource.openai.azure.com/",
    "api_key": "your-api-key",                  # or omit and use DefaultAzureCredential
    "azure_deployment": "gpt-4o",               # your deployment name
    "api_version": "2024-08-01-preview",
}

# Required for safety evaluators
azure_ai_project = {
    "subscription_id": "your-subscription-id",
    "resource_group_name": "myRG",
    "project_name": "my-foundry-project",
}
```

## Built-in evaluators

```python
from azure.ai.evaluation import (
    # Quality — AI-assisted (requires model_config)
    GroundednessEvaluator, RelevanceEvaluator, CoherenceEvaluator,
    FluencyEvaluator, SimilarityEvaluator,
    # Quality — NLP (no model needed)
    BleuScoreEvaluator, RougeScoreEvaluator, F1ScoreEvaluator,
    # Safety (requires azure_ai_project)
    ViolenceEvaluator, HateUnfairnessEvaluator, ContentSafetyEvaluator,
    # Composite
    QAEvaluator,
)

# Instantiate
groundedness = GroundednessEvaluator(model_config=model_config)
bleu = BleuScoreEvaluator()
violence = ViolenceEvaluator(azure_ai_project=azure_ai_project)
```

## Single evaluation

```python
# AI-assisted evaluator
result = groundedness(
    response="Paris is the capital of France.",
    context="France is a country in Europe. Its capital is Paris.",
)
print(result["groundedness"])         # score (1–5 or 0–1 depending on evaluator)
print(result["groundedness_reason"])  # explanation string

# NLP evaluator
result = bleu(
    response="The cat sat on the mat.",
    ground_truth="The cat is on the mat.",
)
print(result["bleu_score"])
```

## Batch evaluation — evaluate()

```python
from azure.ai.evaluation import evaluate

# Dataset evaluation (no target function)
result = evaluate(
    data=[
        {"query": "What is Paris?", "response": "Paris is the capital of France.", "context": "France..."},
        {"query": "What is Berlin?", "response": "Berlin is the capital of Germany.", "context": "Germany..."},
    ],
    evaluators={
        "groundedness": GroundednessEvaluator(model_config=model_config),
        "bleu":         BleuScoreEvaluator(),
    },
    evaluator_config={
        "groundedness": {
            "column_mapping": {
                "response": "${data.response}",  # ${data.field} for dataset columns
                "context":  "${data.context}",
            }
        }
    },
)

# Access results
print(result["metrics"])   # aggregated scores
for row in result["rows"]:
    print(row["groundedness"], row["bleu_score"])
```

## Evaluate with target function

```python
def my_rag_app(query: str) -> dict:
    """Your application — returns dict with response and context."""
    context = retrieve(query)
    response = generate(query, context)
    return {"response": response, "context": context}

result = evaluate(
    data="eval_data.jsonl",     # path to JSONL file with {"query": "..."} rows
    target=my_rag_app,          # function is called with each row's columns
    evaluators={
        "groundedness": GroundednessEvaluator(model_config=model_config),
    },
    evaluator_config={
        "groundedness": {
            "column_mapping": {
                "response": "${outputs.response}",  # ${outputs.field} for target outputs
                "context":  "${outputs.context}",
            }
        }
    },
    output_path="eval_results.jsonl",   # save row-level results
)
```

## Custom evaluator

```python
class ExactMatchEvaluator:
    def __call__(self, *, response: str, ground_truth: str, **kwargs) -> dict:
        match = response.strip().lower() == ground_truth.strip().lower()
        return {"exact_match": 1.0 if match else 0.0}

result = evaluate(
    data=my_data,
    evaluators={"exact_match": ExactMatchEvaluator()},
    evaluator_config={"exact_match": {"column_mapping": {
        "response": "${data.response}",
        "ground_truth": "${data.ground_truth}",
    }}},
)
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `model_config = ModelConfiguration(...)` | `model_config = {...}` — plain dict |
| `column_mapping: {"response": "response"}` | `column_mapping: {"response": "${data.response}"}` |
| `column_mapping: {"response": "${outputs.response}"}` for dataset eval | Use `${data.response}` when no target function |
| `result["groundedness_score"]` | `result["groundedness"]` — field name matches evaluator key |
| Safety evaluators without `azure_ai_project` | Safety evals require `azure_ai_project` parameter |
| Expecting LLM auto-detection | Must explicitly configure `model_config` |
