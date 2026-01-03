# KnowledgeBeast MCP Agent - Task Definition

**Mission:** Wrap KnowledgeBeast RAG system as MCP server with per-project isolation
**Worktree:** worktrees/knowledgebeast-mcp-agent
**Branch:** feature/knowledgebeast-mcp
**Estimated Time:** 25 hours
**Dependencies:** None (Phase 1 - Independent)

---

## Tasks Checklist

### Task 1: Create KnowledgeBeast MCP Server (10 hours)
- [ ] Create `.commandcenter/mcp-servers/knowledgebeast/` directory
- [ ] Implement MCP server wrapper for RAG service
- [ ] Add per-project collection isolation
- [ ] Create document ingestion tools
- [ ] Implement semantic search tools
- [ ] Add knowledge statistics tools
- [ ] Create document management tools
- [ ] Implement embedding generation

**Directory Structure:**
```
.commandcenter/mcp-servers/knowledgebeast/
├── __init__.py
├── server.py              # Main MCP server
├── tools/
│   ├── __init__.py
│   ├── ingest.py          # Document ingestion
│   ├── search.py          # Semantic search
│   ├── manage.py          # Document management
│   └── stats.py           # Knowledge statistics
├── resources/
│   ├── __init__.py
│   ├── knowledge_base.py  # Knowledge base resource
│   └── collections.py     # Collections resource
└── config.py              # Server configuration
```

**Files to Create:**
- `.commandcenter/mcp-servers/knowledgebeast/server.py`
- `.commandcenter/mcp-servers/knowledgebeast/tools/` (4 files)
- `.commandcenter/mcp-servers/knowledgebeast/resources/` (2 files)
- `.commandcenter/mcp-servers/knowledgebeast/config.py`

**Tools to Implement:**
1. `ingest_document` - Add document to knowledge base
2. `search_knowledge` - Semantic search across knowledge base
3. `get_statistics` - Get knowledge base statistics
4. `list_documents` - List all documents in collection
5. `delete_document` - Remove document from knowledge base
6. `update_document` - Update existing document

**Resources to Provide:**
1. `knowledge://base` - Current project knowledge base
2. `knowledge://collections` - All available collections
3. `knowledge://stats` - Knowledge base statistics

---

### Task 2: Implement Per-Project Isolation (5 hours)
- [ ] Wrap existing RAGService with collection_name parameter
- [ ] Create collection naming strategy: `project_{project_id}`
- [ ] Implement collection initialization on first use
- [ ] Add collection switching mechanism
- [ ] Create collection metadata storage
- [ ] Implement isolation verification
- [ ] Add cross-collection prevention

**Implementation:**
```python
class KnowledgeBeastMCP:
    def __init__(self, project_id: str):
        self.collection_name = f"project_{project_id}"
        self.rag_service = RAGService(collection_name=self.collection_name)

    async def ensure_isolated(self):
        # Verify collection isolation
        # Prevent cross-project access
        pass
```

**Files to Modify:**
- `backend/app/services/rag_service.py` (add collection_name parameter)
- `.commandcenter/mcp-servers/knowledgebeast/server.py` (isolation logic)

**Validation:**
- Each project gets unique collection
- No cross-project data leakage
- Collection metadata tracked
- Automatic collection initialization

---

### Task 3: Integrate Docling Document Processing (5 hours)
- [ ] Wrap existing Docling service in MCP tools
- [ ] Add support for multiple document formats (PDF, MD, TXT, DOCX)
- [ ] Implement batch document processing
- [ ] Create document chunking strategy
- [ ] Add metadata extraction
- [ ] Implement progress tracking for large documents
- [ ] Add error handling for corrupt documents

**Tools to Implement:**
1. `process_document` - Process single document with Docling
2. `batch_process` - Process multiple documents
3. `extract_metadata` - Extract document metadata
4. `chunk_document` - Chunk document for embedding

**Files to Create:**
- `.commandcenter/mcp-servers/knowledgebeast/tools/docling.py`

**Supported Formats:**
- PDF (via Docling)
- Markdown (.md)
- Plain text (.txt)
- Word documents (.docx)
- Code files (auto-detected)

---

### Task 4: Create Context7-Style Documentation Integration (3 hours)
- [ ] Design documentation source configuration
- [ ] Create documentation crawler for Anthropic docs
- [ ] Add GitHub repository documentation ingestion
- [ ] Implement automatic documentation updates
- [ ] Create documentation versioning
- [ ] Add documentation search optimization

**Documentation Sources:**
```json
{
  "sources": [
    {
      "type": "anthropic_docs",
      "url": "https://docs.anthropic.com",
      "auto_update": true,
      "priority": "high"
    },
    {
      "type": "github_repo",
      "repo": "owner/repo",
      "paths": ["docs/", "README.md"],
      "auto_update": true
    },
    {
      "type": "local",
      "path": "./docs",
      "watch": true
    }
  ]
}
```

**Files to Create:**
- `.commandcenter/mcp-servers/knowledgebeast/tools/doc_crawler.py`
- `.commandcenter/knowledge/sources.json`

**Implementation:**
- Crawl Anthropic docs (starting point)
- Auto-update on new versions
- Prioritized search results
- Version tracking

---

### Task 5: Add Slash Command Integration (2 hours)
- [ ] Create `.claude/commands/research.md` command
- [ ] Create `.claude/commands/ingest-docs.md` command
- [ ] Create `.claude/commands/knowledge-stats.md` command
- [ ] Map commands to KnowledgeBeast MCP tools
- [ ] Add command documentation

**Slash Commands to Create:**
1. `/research <query>` - Search knowledge base
2. `/ingest-docs <path>` - Ingest documents into knowledge base
3. `/knowledge-stats` - Show knowledge base statistics

**Files to Create:**
- `.claude/commands/research.md`
- `.claude/commands/ingest-docs.md`
- `.claude/commands/knowledge-stats.md`

**Command Mapping:**
- `/research` → `search_knowledge` tool
- `/ingest-docs` → `ingest_document` tool
- `/knowledge-stats` → `get_statistics` tool

---

## Testing Requirements

### Unit Tests to Write
- [ ] `tests/mcp/test_knowledgebeast_server.py` - MCP server
- [ ] `tests/mcp/test_isolation.py` - Per-project isolation
- [ ] `tests/mcp/test_docling_integration.py` - Document processing
- [ ] `tests/mcp/test_search.py` - Semantic search

### Integration Tests
- [ ] Test collection isolation (multiple projects)
- [ ] Test document ingestion flow
- [ ] Test semantic search accuracy
- [ ] Test Docling processing pipeline
- [ ] Test slash command integration

### Isolation Validation
- [ ] Create test project A and B
- [ ] Ingest different documents in each
- [ ] Verify no cross-project search results
- [ ] Verify separate embeddings

---

## Review Checklist

Before creating PR, ensure:
- [ ] All tests pass: `pytest tests/mcp/`
- [ ] Per-project isolation verified
- [ ] Semantic search working
- [ ] Docling integration functional
- [ ] Slash commands operational
- [ ] Documentation complete
- [ ] Run `/review` until score is 10/10

---

## PR Details

**Title:** "MCP: KnowledgeBeast RAG server with per-project isolation"

**Description:**
```markdown
## KnowledgeBeast MCP Server Complete ✅

This PR wraps the existing KnowledgeBeast RAG system as an MCP server with per-project isolation.

### Changes
- ✅ KnowledgeBeast MCP server with 6 core tools
- ✅ Per-project collection isolation (project_{id})
- ✅ Docling document processing integration
- ✅ Context7-style documentation ingestion
- ✅ Slash command integration (3 commands)

### MCP Tools Implemented
1. `ingest_document` - Add documents to knowledge base
2. `search_knowledge` - Semantic search with RAG
3. `get_statistics` - Knowledge base statistics
4. `list_documents` - List all documents
5. `delete_document` - Remove documents
6. `update_document` - Update documents

### Per-Project Isolation
- Unique ChromaDB collection per project
- Collection naming: `project_{project_id}`
- No cross-project data leakage
- Automatic collection initialization

### Slash Commands Added
- `/research <query>` - Search knowledge base
- `/ingest-docs <path>` - Ingest documents
- `/knowledge-stats` - Show statistics

### Supported Document Formats
- PDF (via Docling)
- Markdown (.md)
- Plain text (.txt)
- Word documents (.docx)
- Code files (auto-detected)

### Review Score: 10/10 ✅
```

---

## Success Criteria

- [ ] KnowledgeBeast MCP server operational
- [ ] Per-project isolation verified
- [ ] Document ingestion working
- [ ] Semantic search functional
- [ ] Docling integration complete
- [ ] Slash commands working
- [ ] All tests passing (>90% coverage)
- [ ] Review score 10/10
- [ ] No merge conflicts
- [ ] PR approved and merged

---

**Reference Documents:**
- `.claude/memory.md` (Session 2 - MCP architecture planning)
- `backend/app/services/rag_service.py` (existing RAG implementation)
- `docs/DOCLING_SETUP.md` (Docling documentation)
