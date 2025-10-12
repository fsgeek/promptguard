#!/usr/bin/env python3
"""Verify model import to ArangoDB."""

from arango import ArangoClient
import os

client = ArangoClient(hosts='http://192.168.111.125:8529')
db = client.db('PromptGuard', username='pgtest', password=os.environ['ARANGODB_PROMPTGUARD_PASSWORD'])
coll = db.collection('models')

# Count documents
print(f'Total models in collection: {coll.count()}')

# Sample a few priority models
priority = [
    'moonshotai_kimi-k2-0905',
    'anthropic_claude-sonnet-4.5',
    'openai_gpt-5-codex',
    'deepseek_deepseek-r1'
]

print('\nPriority model samples:')
for key in priority:
    try:
        doc = coll.get(key)
        print(f'  {key}:')
        print(f'    Name: {doc["name"]}')
        print(f'    Type: {doc["model_type"]}')
        print(f'    Observer: {doc["observer_framing_compatible"]}')
        print(f'    Cost: ${doc["cost_per_1m_input"]}/{doc["cost_per_1m_output"]} per 1M tokens')
    except Exception as e:
        print(f'  {key}: ERROR - {e}')

# Count by model type
print('\nModels by type:')
cursor = db.aql.execute('''
    FOR doc IN models
    COLLECT type = doc.model_type WITH COUNT INTO count
    SORT count DESC
    RETURN {type: type, count: count}
''')
for row in cursor:
    print(f'  {row["type"]}: {row["count"]}')

# Count by observer framing
print('\nObserver framing compatibility:')
cursor = db.aql.execute('''
    FOR doc IN models
    COLLECT compat = doc.observer_framing_compatible WITH COUNT INTO count
    SORT count DESC
    RETURN {compat: compat, count: count}
''')
for row in cursor:
    print(f'  {row["compat"]}: {row["count"]}')
