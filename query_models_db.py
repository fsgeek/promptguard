#!/usr/bin/env python3
"""Query models collection from ArangoDB to see current/flagship models."""

import os
from arango import ArangoClient

# Connect to ArangoDB
client = ArangoClient(
    hosts=f"http://{os.getenv('ARANGODB_HOST', '192.168.111.125')}:{os.getenv('ARANGODB_PORT', '8529')}"
)

# Authenticate
db = client.db(
    os.getenv("ARANGODB_DB", "PromptGuard"),
    username=os.getenv("ARANGODB_USER", "pgtest"),
    password=os.getenv("ARANGODB_PROMPTGUARD_PASSWORD")
)

# Query for current flagship models
aql = """
FOR m IN models
    FILTER m.is_current == true OR m.is_flagship == true
    SORT m.organization, m.name
    RETURN {
        name: m.name,
        organization: m.organization,
        is_current: m.is_current,
        is_flagship: m.is_flagship,
        observer_compatible: m.observer_compatible,
        input_cost_per_1m: m.pricing.input_per_1m_tokens,
        output_cost_per_1m: m.pricing.output_per_1m_tokens
    }
"""

cursor = db.aql.execute(aql)
models = list(cursor)

print("Current/Flagship Models in ArangoDB:")
print("=" * 80)
for m in models:
    flags = []
    if m.get("is_current"):
        flags.append("CURRENT")
    if m.get("is_flagship"):
        flags.append("FLAGSHIP")
    if m.get("observer_compatible"):
        flags.append("OBSERVER")
    
    flag_str = f"[{', '.join(flags)}]" if flags else ""
    print(f"{m['organization']}/{m['name']} {flag_str}")
    print(f"  Cost: ${m['input_cost_per_1m']:.2f} in / ${m['output_cost_per_1m']:.2f} out per 1M tokens")
    print()
