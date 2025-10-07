# Ingest Docs Command

Ingest documents into the KnowledgeBeast knowledge base.

## Usage

```
/ingest-docs <path> [category]
```

## Description

This command ingests documents from a file or directory into the project's knowledge base. It supports multiple document formats and automatically chunks, embeds, and indexes the content for semantic search.

## Examples

```
/ingest-docs ./docs/
/ingest-docs ./README.md documentation
/ingest-docs ./backend/app/services/ code
```

## Supported Formats

- **Markdown** (.md, .markdown)
- **PDF** (.pdf) - via Docling
- **Microsoft Word** (.docx)
- **Plain Text** (.txt)
- **Code** (.py, .js, .ts, .java, .cpp, .c, .go, .rs)
- **JSON/YAML** (.json, .yaml, .yml)

## Parameters

- **path** (required): File or directory path to ingest
- **category** (optional): Category for organizing documents (default: auto-detected)

## How It Works

1. Scans the specified path for supported file types
2. Processes each document using appropriate handler:
   - PDFs use Docling for intelligent extraction
   - Code files preserve syntax and structure
   - Markdown preserves formatting
3. Documents are chunked into 1000-character segments with 200-character overlap
4. Each chunk is embedded using HuggingFace Sentence Transformers
5. Embeddings are stored in ChromaDB with per-project isolation

## Output

Returns ingestion summary:
- Number of files processed
- Total chunks created
- Category breakdown
- Any errors encountered

## Examples

### Ingest Documentation Directory
```
/ingest-docs ./docs/ documentation
```

### Ingest Single File
```
/ingest-docs ./ARCHITECTURE.md architecture
```

### Ingest Code Directory
```
/ingest-docs ./backend/app/services/ code
```

## Related Commands

- `/research` - Search the knowledge base
- `/knowledge-stats` - View ingestion statistics

## Technical Details

This command uses the `ingest_document` tool from the KnowledgeBeast MCP server with:
- Per-project collection isolation (collection name: `project_{id}`)
- RecursiveCharacterTextSplitter for intelligent chunking
- HuggingFace embeddings (all-MiniLM-L6-v2)
- ChromaDB persistent storage
