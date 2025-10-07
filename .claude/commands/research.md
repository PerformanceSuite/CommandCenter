# Research Command

Search the KnowledgeBeast knowledge base using semantic search.

## Usage

```
/research <query>
```

## Description

This command performs a semantic search across the project's knowledge base using the KnowledgeBeast MCP server. It uses RAG (Retrieval-Augmented Generation) to find relevant information based on natural language queries.

## Examples

```
/research How do I configure the database connection?
/research Best practices for error handling in FastAPI
/research What is the authentication flow?
```

## How It Works

1. The query is embedded using HuggingFace Sentence Transformers
2. Semantic similarity search is performed against the ChromaDB vector store
3. Top-k most relevant document chunks are returned with scores
4. Results are formatted with source information and relevance scores

## Parameters

- **query** (required): Natural language search query

## Output

Returns the top 5 most relevant results including:
- Document source
- Category
- Relevance score
- Content excerpt

## Related Commands

- `/ingest-docs` - Add documents to the knowledge base
- `/knowledge-stats` - View knowledge base statistics

## Technical Details

This command uses the `search_knowledge` tool from the KnowledgeBeast MCP server with per-project collection isolation.
