#!/usr/bin/env python3
"""
Decrypt and analyze target LLM responses.

Provides utilities for:
- Decrypting specific responses for analysis
- Querying responses by model, label, outcome
- Exporting analysis datasets (with decrypted text)

IMPORTANT: Never commit decrypted data to git.

Usage:
    # Get specific response
    python decrypt_responses.py --prompt benign_malicious_264951 --model anthropic/claude-sonnet-4.5

    # Export all COMPLIED responses for manipulative prompts
    python decrypt_responses.py --export --label manipulative --outcome COMPLIED --output analysis_data.json

    # Query by model
    python decrypt_responses.py --model openai/gpt-4o --limit 10
"""

import json
import argparse
from typing import Optional, List
from pathlib import Path

from promptguard.storage.target_response_storage import TargetResponseStorage


def get_response(
    storage: TargetResponseStorage,
    prompt_id: str,
    model: str
) -> None:
    """Retrieve and display single response."""
    response = storage.get_response(prompt_id, model, decrypt=True)

    if not response:
        print(f"No response found for {prompt_id}/{model}")
        return

    # Display
    print("=" * 80)
    print(f"Prompt ID: {response['prompt_id']}")
    print(f"Label: {response['prompt_label']}")
    print(f"Model: {response['target_model']}")
    print("-" * 80)
    print("PROMPT:")
    print(response['prompt_text'])
    print("-" * 80)
    print("RESPONSE:")
    print(response['response']['text'])
    print("=" * 80)
    print(f"Tokens: {response['response']['tokens']}")
    print(f"Latency: {response['response']['latency_ms']}ms")
    print(f"Cost: ${response['response']['cost_usd']:.4f}")


def query_responses(
    storage: TargetResponseStorage,
    model: Optional[str] = None,
    label: Optional[str] = None,
    limit: int = 10
) -> List[dict]:
    """
    Query responses with filters.

    Args:
        storage: Storage backend
        model: Filter by target model
        label: Filter by prompt label
        limit: Maximum results

    Returns:
        List of response documents
    """
    # Build AQL query
    filters = []
    bind_vars = {"limit": limit}

    if model:
        filters.append("doc.target_model == @model")
        bind_vars["model"] = model

    if label:
        filters.append("doc.prompt_label == @label")
        bind_vars["label"] = label

    filter_clause = " AND ".join(filters) if filters else "true"

    query = f"""
    FOR doc IN target_responses
        FILTER {filter_clause}
        LIMIT @limit
        RETURN doc
    """

    cursor = storage.db.aql.execute(query, bind_vars=bind_vars)
    return list(cursor)


def export_responses(
    storage: TargetResponseStorage,
    output_path: str,
    model: Optional[str] = None,
    label: Optional[str] = None,
    decrypt: bool = True
) -> None:
    """
    Export filtered responses to JSON file.

    Args:
        storage: Storage backend
        output_path: Where to write JSON
        model: Filter by target model
        label: Filter by prompt label
        decrypt: Whether to decrypt response text
    """
    # Query all matching responses (no limit for export)
    filters = []
    bind_vars = {}

    if model:
        filters.append("doc.target_model == @model")
        bind_vars["model"] = model

    if label:
        filters.append("doc.prompt_label == @label")
        bind_vars["label"] = label

    filter_clause = " AND ".join(filters) if filters else "true"

    query = f"""
    FOR doc IN target_responses
        FILTER {filter_clause}
        RETURN doc
    """

    cursor = storage.db.aql.execute(query, bind_vars=bind_vars)
    responses = list(cursor)

    # Decrypt if requested
    if decrypt:
        for response in responses:
            if "text_encrypted" in response.get("response", {}):
                encrypted = response["response"]["text_encrypted"]
                response["response"]["text"] = storage.encryption.decrypt(encrypted)
                del response["response"]["text_encrypted"]

    # Write to file
    output = {
        "filters": {
            "model": model,
            "label": label
        },
        "count": len(responses),
        "responses": responses
    }

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Exported {len(responses)} responses to {output_path}")
    print(f"WARNING: {output_path} contains decrypted data. Do NOT commit to git.")


def main():
    parser = argparse.ArgumentParser(description="Decrypt and analyze target responses")

    # Query options
    parser.add_argument("--prompt", help="Prompt ID to retrieve")
    parser.add_argument("--model", help="Filter by target model")
    parser.add_argument("--label", help="Filter by prompt label")
    parser.add_argument("--limit", type=int, default=10, help="Max results for queries")

    # Export options
    parser.add_argument("--export", action="store_true", help="Export to JSON file")
    parser.add_argument("--output", default="decrypted_responses.json", help="Output file for export")
    parser.add_argument("--no-decrypt", action="store_true", help="Keep responses encrypted in export")

    args = parser.parse_args()

    # Initialize storage
    storage = TargetResponseStorage()

    # Single response retrieval
    if args.prompt:
        if not args.model:
            print("ERROR: --model required when using --prompt")
            return
        get_response(storage, args.prompt, args.model)
        return

    # Export mode
    if args.export:
        export_responses(
            storage,
            args.output,
            model=args.model,
            label=args.label,
            decrypt=not args.no_decrypt
        )
        return

    # Query mode
    responses = query_responses(
        storage,
        model=args.model,
        label=args.label,
        limit=args.limit
    )

    print(f"Found {len(responses)} responses:")
    print("=" * 80)

    for response in responses:
        tokens = response['response']['tokens']
        latency = response['response']['latency_ms']
        print(f"{response['prompt_id']:30} | {response['target_model']:40} | {tokens:5d} tokens | {latency:5d}ms")

    if responses:
        print("=" * 80)
        print("Use --prompt and --model to view full response")


if __name__ == "__main__":
    main()
