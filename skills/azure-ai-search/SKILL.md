---
name: azure-ai-search
description: >
  Azure AI Search SDK for Python (`azure-search-documents`). Use this skill for full-text search,
  vector search, hybrid search, semantic ranking, index management, and document ingestion with
  Azure AI Search. Triggers on: "azure-search-documents", "SearchClient", "SearchIndexClient",
  "vector search", "hybrid search", "semantic search", "semantic ranking", "AI Search", "cognitive search",
  "search index", "SearchField", "VectorizedQuery", "VectorizableTextQuery", "search index",
  "indexer", "skillset", "facets", "OData filter". Use whenever building search features with
  Azure — even if the user just says "add search to my app" or "set up vector search in Azure".
---

# Azure AI Search SDK for Python

Build full-text, vector, hybrid, and semantic search experiences using `azure-search-documents`.

## Installation

```bash
pip install azure-search-documents azure-identity
```

## Three clients to know

| Client | Use for | Import |
|--------|---------|--------|
| `SearchClient` | Search queries + document upload | `azure.search.documents` |
| `SearchIndexClient` | Index schema management | `azure.search.documents.indexes` |
| `SearchIndexerClient` | Indexers + skillsets | `azure.search.documents.indexes` |

## Endpoint format

```
https://<service-name>.search.windows.net
```
Not the Azure Portal URL, not the resource ID — just that base URL.

## Authentication

```python
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

# Dev / quick start
credential = AzureKeyCredential("your-admin-or-query-key")

# Production (managed identity / service principal)
credential = DefaultAzureCredential()
```

---

## SearchClient — queries and documents

```python
from azure.search.documents import SearchClient

client = SearchClient(
    endpoint="https://myservice.search.windows.net",
    index_name="my-index",
    credential=AzureKeyCredential("key")
)
```

### Full-text search

```python
results = client.search(
    search_text="luxury hotels near Seattle",
    search_fields=["Description", "Name"],  # WHERE to search (default: all searchable)
    select=["Name", "Rating", "Category"],  # WHAT fields to return
    filter="Rating ge 4 and Category eq 'Luxury'",
    order_by=["Rating desc"],
    top=10,
    skip=0,
    facets=["Category,count:5", "Rating,interval:1"],
)

for result in results:
    print(result["Name"], result["@search.score"])

# Facet counts live on the response object, not individual results
facets = results.get_facets()
```

`search_text="*"` returns all documents. Results are `SearchItemPaged` — iterate with `for` or `list()`.

### Vector search (pure)

```python
from azure.search.documents.models import VectorizedQuery

query = VectorizedQuery(
    vector=embedding,            # list[float] — pre-computed embedding
    k_nearest_neighbors=5,
    fields="content_vector",     # The vector field in your index
    exhaustive=False,            # True = brute-force kNN (slower, exact)
)

results = client.search(
    search_text=None,            # None = pure vector, no text scoring
    vector_queries=[query],
    select=["id", "content", "title"],
    top=5,
)
```

### Hybrid search (text + vector combined — recommended)

Hybrid search merges full-text BM25 scores with vector similarity using Reciprocal Rank Fusion (RRF). It consistently outperforms either alone:

```python
results = client.search(
    search_text="luxury hotels",         # BM25 text search
    vector_queries=[VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=50,          # Larger candidate set for RRF merging
        fields="content_vector",
    )],
    select=["id", "title", "content"],
    top=10,
)
```

### Hybrid + semantic reranking (best quality)

Semantic ranking applies a language model to rerank the top results from hybrid search:

```python
results = client.search(
    search_text="what makes a luxury hotel?",
    vector_queries=[VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=50,
        fields="content_vector",
    )],
    query_type="semantic",                          # Enables semantic reranking
    semantic_configuration_name="my-semantic-cfg",  # Must match index config
    query_caption="extractive",                     # Extract passage captions
    query_answer="extractive",                      # Extract answer snippet
    top=5,
)

for result in results:
    print(f"Score: {result['@search.reranker_score']}")
    captions = result.get("@search.captions", [])
    if captions:
        print(f"Caption: {captions[0]['text']}")

# Top answer (if found)
answers = results.get_answers()
if answers:
    print(f"Answer: {answers[0].text}")
```

Semantic reranking requires the index to have a `SemanticConfiguration` defined (see index setup below).

### Vector filter modes

When combining vector search with filters, choose the mode based on your needs:

```python
from azure.search.documents.models import VectorFilterMode

# PreFilter (default recommended): apply OData filter BEFORE vector search
# → Guarantees top-k results all satisfy the filter; may return fewer than k
results = client.search(
    search_text="*",
    vector_queries=[VectorizedQuery(vector=emb, k_nearest_neighbors=10, fields="vec")],
    filter="Category eq 'Electronics'",
    vector_filter_mode=VectorFilterMode.PRE_FILTER,  # default
)
```

### Document operations

```python
# Upload (insert or replace)
results = client.upload_documents(documents=[
    {"id": "1", "title": "Azure Search", "content": "...", "content_vector": [0.1, ...]},
    {"id": "2", "title": "Vector Search", "content": "...", "content_vector": [0.2, ...]},
])

# Partial update (only specified fields updated)
results = client.merge_documents(documents=[
    {"id": "1", "rating": 4.5}   # Only updates rating field
])

# Upsert — most common for ingestion pipelines
results = client.merge_or_upload_documents(documents=[...])

# Delete (only key field required)
results = client.delete_documents(documents=[{"id": "1"}, {"id": "2"}])

# Check results
for r in results:
    if not r.succeeded:
        print(f"Failed: {r.key} — {r.error_message}")
```

Batch limit: 1,000 documents or ~16 MB per call.

### High-throughput ingestion (`SearchIndexingBufferedSender`)

For large datasets, use the buffered sender which handles batching and retries automatically:

```python
from azure.search.documents import SearchIndexingBufferedSender

with SearchIndexingBufferedSender(
    endpoint, index_name, credential,
    auto_flush=True,
    auto_flush_interval=60,
) as sender:
    for doc in large_dataset:
        sender.upload_documents([doc])   # Buffers and auto-flushes
```

---

## SearchIndexClient — index schema management

```python
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchField,
    SearchFieldDataType, VectorSearch, HnswAlgorithmConfiguration,
    VectorSearchProfile, SemanticConfiguration, SemanticSearch,
    SemanticPrioritizedFields, SemanticField,
)

index_client = SearchIndexClient(endpoint, credential)
```

### Define an index with vector + semantic support

```python
index = SearchIndex(
    name="my-index",
    fields=[
        SimpleField(name="id", type="Edm.String", key=True, filterable=True),
        SearchableField(name="title", type="Edm.String", analyzer_name="en.microsoft"),
        SearchableField(name="content", type="Edm.String"),
        SimpleField(name="category", type="Edm.String", filterable=True, facetable=True),
        SimpleField(name="rating", type="Edm.Double", filterable=True, sortable=True),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,           # Must match your embedding model
            vector_search_profile_name="my-profile", # Links to VectorSearchProfile below
        ),
    ],
    vector_search=VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="my-hnsw")],
        profiles=[VectorSearchProfile(
            name="my-profile",
            algorithm_configuration_name="my-hnsw",
        )],
    ),
    semantic_search=SemanticSearch(
        configurations=[SemanticConfiguration(
            name="my-semantic-cfg",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="title"),
                content_fields=[SemanticField(field_name="content")],
                keywords_fields=[SemanticField(field_name="category")],
            ),
        )]
    ),
)

index_client.create_or_update_index(index)
```

**Exactly one field must have `key=True`** — this is the document identifier.

### Index CRUD

```python
index_client.get_index("my-index")
list(index_client.list_index_names())
list(index_client.list_indexes())
index_client.delete_index("my-index")
```

---

## Async clients

```python
from azure.search.documents.aio import SearchClient as AsyncSearchClient
from azure.search.documents.indexes.aio import SearchIndexClient as AsyncSearchIndexClient

async def search_async(query_text: str, embedding: list[float]):
    async with AsyncSearchClient(endpoint, index_name, credential) as client:
        results = await client.search(
            search_text=query_text,
            vector_queries=[VectorizedQuery(vector=embedding, k_nearest_neighbors=10,
                                            fields="content_vector")],
        )
        async for result in results:
            print(result["title"])
```

---

## OData filter syntax

```python
# Equality / inequality
filter="Category eq 'Luxury'"
filter="Rating gt 4 and Rating le 5"
filter="Category ne 'Budget'"

# Logical
filter="(Category eq 'Luxury' or Category eq 'Premium') and Rating ge 4"

# Collections — any() / all()
filter="Tags/any(t: t eq 'wifi')"
filter="Tags/all(t: t ne 'smoking')"

# Negation
filter="not (Category eq 'Budget')"

# Null checks
filter="Description ne null"
```

`search_fields` = which fields to search within (relevance). `filter` = hard exclusion. `select` = which fields to return in each result.

---

## Common mistakes

| Mistake | Effect | Fix |
|---------|--------|-----|
| Endpoint missing `https://` or wrong domain | `ServiceRequestError` | `https://<name>.search.windows.net` |
| `vector` field is a string or JSON | `HttpResponseError: 400` | Must be `list[float]` |
| Vector field not in index schema with `vector_search_dimensions` | `HttpResponseError: 400` | Add `SearchField` with dimensions + profile |
| `query_type="semantic"` without `semantic_configuration_name` | 400 error | Always provide both together |
| Semantic config name doesn't match index definition | 400 error | Name must match exactly |
| No `key=True` field in index | Index creation fails | Exactly one `SimpleField` with `key=True` |
| `select=["field"]` for non-existent field | Empty results or error | Field must be in index and `retrievable=True` |
| `search_fields` includes non-searchable field | Silent no-op or error | Only `SearchableField` or `searchable=True` |
| `vector_search_dimensions` mismatch with embeddings | 400 error | Dimensions must match your embedding model output exactly |
| `merge_documents` on non-existent document | `IndexingResult` with error | Use `merge_or_upload_documents` for upserts |
