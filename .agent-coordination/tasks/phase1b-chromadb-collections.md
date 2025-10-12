# Phase 1b: ChromaDB Collections Agent

## Mission
Create per-project ChromaDB collections for knowledge base isolation.

## Priority
CRITICAL - Prevents knowledge base data leaks

## Estimated Time
4 hours

## Tasks

### 1. Update RAGService (2 hours)
```python
# backend/app/services/rag_service.py

class RAGService:
    def _get_collection_name(self, project_id: int) -> str:
        """Get collection name for project"""
        return f"knowledge_project_{project_id}"
    
    def get_collection(self, project_id: int):
        """Get or create collection for project"""
        collection_name = self._get_collection_name(project_id)
        
        try:
            return self.chroma_client.get_collection(name=collection_name)
        except:
            return self.chroma_client.create_collection(
                name=collection_name,
                metadata={"project_id": project_id}
            )
    
    async def query(self, project_id: int, query_text: str, n_results: int = 5):
        """Query project's collection only"""
        collection = self.get_collection(project_id)
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results
```

### 2. Update Knowledge Endpoints (1 hour)
Update all knowledge endpoints to:
- Extract project_id from request context
- Pass project_id to RAGService methods
- Use project-specific collection

Files to update:
- `backend/app/routers/knowledge.py`
- `backend/app/services/rag_service.py`

### 3. Add Collection Management (30 min)
Add endpoints:
- List collections for project
- Delete collection (when project deleted)
- Get collection stats (doc count, etc.)

### 4. Migrate Existing Data (30 min)
Create migration script to move existing embeddings to default project collection

## Success Criteria
- ✅ Each project has own collection
- ✅ Queries only search project's collection
- ✅ No cross-project knowledge leaks
- ✅ Existing data migrated
- ✅ Tests pass
