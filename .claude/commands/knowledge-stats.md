# Knowledge Stats Command

View statistics about the KnowledgeBeast knowledge base.

## Usage

```
/knowledge-stats
```

## Description

This command displays comprehensive statistics about the project's knowledge base, including document counts, categories, collection information, and embedding details.

## Examples

```
/knowledge-stats
```

## Output

Returns detailed statistics:

### Collection Information
- Collection name (with project isolation)
- Database path
- Embedding model in use

### Document Metrics
- Total documents ingested
- Total chunks/embeddings
- Documents per category

### Category Breakdown
- List of all categories
- Document count per category
- Chunk count per category

### Technical Details
- Embedding model name and type
- Vector dimension size
- Storage location

## Example Output

```
Knowledge Base Statistics for 'commandcenter':

Collection: project_commandcenter
Total Chunks: 1,234
Total Documents: 56
Embedding Model: sentence-transformers/all-MiniLM-L6-v2
Database Path: ./rag_storage

Categories:
  - documentation: 892 chunks (23 documents)
  - code: 234 chunks (18 documents)
  - architecture: 108 chunks (15 documents)
```

## Use Cases

- **Before searching**: Check what's in the knowledge base
- **After ingestion**: Verify documents were added
- **Capacity planning**: Monitor knowledge base size
- **Debugging**: Ensure per-project isolation is working

## Related Commands

- `/research` - Search the knowledge base
- `/ingest-docs` - Add documents to the knowledge base

## Technical Details

This command uses the `get_statistics` tool from the KnowledgeBeast MCP server.

### Per-Project Isolation

Each project has its own isolated collection:
- Collection naming: `project_{project_id}`
- No cross-project data leakage
- Independent embeddings and metadata

### Performance Notes

Statistics are computed in real-time from ChromaDB. For large knowledge bases (>100k chunks), this may take a few seconds.
