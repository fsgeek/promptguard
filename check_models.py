import os
from arango import ArangoClient

client = ArangoClient(hosts=f"http://{os.getenv('ARANGODB_HOST', '192.168.111.125')}:{os.getenv('ARANGODB_PORT', '8529')}")
db = client.db(os.getenv("ARANGODB_DB", "PromptGuard"), username=os.getenv("ARANGODB_USER", "pgtest"), password=os.getenv("ARANGODB_PROMPTGUARD_PASSWORD"))

# Get all models
aql = "FOR m IN models LIMIT 5 RETURN m"
cursor = db.aql.execute(aql)
models = list(cursor)

print(f"Total models: {db.collection('models').count()}")
print("\nFirst 5 models:")
for m in models:
    print(f"  {m.get('name', 'NO NAME')} - is_current={m.get('is_current')}, is_flagship={m.get('is_flagship')}")
