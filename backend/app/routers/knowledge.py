"""
Knowledge base and RAG endpoints
Provides access to document storage, retrieval, and semantic search
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import json

from app.database import get_db
from app.models.knowledge_entry import KnowledgeEntry
from app.schemas import (
    KnowledgeEntryCreate,
    KnowledgeEntryResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResult,
)
from app.services.rag_service import RAGService
from app.services.docling_service import DoclingService
from app.services.cache_service import CacheService
from app.config import settings

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# Dependency to get RAG service (KnowledgeBeast PostgresBackend)
async def get_rag_service(
    repository_id: int = 1,  # TODO: Get from auth context/repository context
):
    """
    Get RAG service instance for a specific repository

    Each repository gets its own isolated knowledge base collection.
    The service is automatically initialized before first use.

    Args:
        repository_id: Repository ID for multi-tenant isolation

    Returns:
        Initialized RAGService instance
    """
    service = RAGService(repository_id=repository_id)
    await service.initialize()
    return service


# Legacy dependency for backward compatibility (deprecated)
async def get_knowledge_service(
    repository_id: int = 1,
):
    """Legacy alias for get_rag_service - use get_rag_service instead"""
    return await get_rag_service(repository_id=repository_id)


# Dependency to get Docling service
async def get_docling_service() -> DoclingService:
    """Get Docling service instance"""
    return DoclingService()


# Dependency to get cache service
async def get_cache_service() -> CacheService:
    """Get cache service instance"""
    return CacheService()


@router.post("/query", response_model=List[KnowledgeSearchResult])
async def query_knowledge_base(
    request: KnowledgeSearchRequest,
    repository_id: int = 1,  # TODO: Get from auth context/repository context
    rag_service: RAGService = Depends(get_rag_service),
    cache_service: CacheService = Depends(get_cache_service),
    db: AsyncSession = Depends(get_db),
) -> List[KnowledgeSearchResult]:
    """
    Query the knowledge base using hybrid search (vector + keyword)

    Uses KnowledgeBeast PostgresBackend with hybrid search (70% vector, 30% keyword)
    for optimal retrieval accuracy.

    Args:
        request: Search request with query, filters, and limit
        repository_id: Repository ID for multi-tenant isolation

    Returns:
        List of relevant knowledge entries with scores
    """
    # Create cache key
    cache_key = (
        f"kb_query:{repository_id}:{request.query}:{request.category}:{request.limit}"
    )

    # Try to get from cache first
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        return [KnowledgeSearchResult(**item) for item in json.loads(cached_result)]

    try:
        # Query using RAG service (hybrid search with alpha=0.7)
        results = await rag_service.query(
            question=request.query, category=request.category, k=request.limit
        )

        # Format results
        search_results = []
        for result in results:
            search_results.append(
                KnowledgeSearchResult(
                    content=result["content"],
                    title=result["metadata"].get("title", "Untitled"),
                    category=result["category"],
                    technology_id=result["metadata"].get("technology_id"),
                    source_file=result["source"],
                    score=result["score"],
                    metadata=result["metadata"],
                )
            )

        # Cache the results (5 minute TTL)
        await cache_service.set(
            cache_key,
            json.dumps([r.model_dump() for r in search_results]),
            ttl=300,  # 5 minutes
        )

        return search_results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying knowledge base: {str(e)}",
        )


@router.post(
    "/documents", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED
)
async def add_document(
    file: UploadFile = File(...),
    category: str = Form(...),
    technology_id: Optional[int] = Form(None),
    repository_id: int = Form(1),  # Repository ID for multi-tenant isolation
    rag_service: RAGService = Depends(get_rag_service),
    docling_service: DoclingService = Depends(get_docling_service),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Add a document to the knowledge base

    Supports PDF, Markdown, and text files via Docling processing.
    Documents are automatically chunked, embedded, and indexed in the
    repository-specific knowledge base collection.

    Args:
        file: Uploaded file (PDF, Markdown, or text)
        category: Document category
        technology_id: Optional technology association
        repository_id: Repository ID for multi-tenant isolation

    Returns:
        Document processing summary
    """
    try:
        # Read file content
        content = await file.read()
        filename = file.filename

        # Determine file type
        file_extension = filename.split(".")[-1].lower() if "." in filename else ""

        # Process document with Docling
        if file_extension == "pdf":
            processed_content = await docling_service.process_pdf(content)
        elif file_extension in ["md", "markdown"]:
            processed_content = await docling_service.process_markdown(
                content.decode("utf-8")
            )
        elif file_extension in ["txt", "text"]:
            processed_content = await docling_service.process_text(
                content.decode("utf-8")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension}",
            )

        # Prepare metadata
        metadata = {
            "title": filename,
            "category": category,
            "source": filename,
            "source_type": file_extension,
            "technology_id": technology_id,
        }

        # Add to vector database (uses injected service with correct repository_id)
        chunks_added = await rag_service.add_document(
            content=processed_content, metadata=metadata
        )

        # Create knowledge entry in database
        knowledge_entry = KnowledgeEntry(
            project_id=repository_id,  # Use repository_id as project_id for multi-tenant isolation
            title=filename,
            content=processed_content[:1000],  # Store preview
            category=category,
            technology_id=technology_id,
            source_file=filename,
            source_type=file_extension,
            embedding_model=settings.EMBEDDING_MODEL,  # Updated to use new config
        )

        db.add(knowledge_entry)
        await db.commit()
        await db.refresh(knowledge_entry)

        return {
            "id": knowledge_entry.id,
            "filename": filename,
            "category": category,
            "repository_id": repository_id,
            "collection": f"commandcenter_{repository_id}",
            "chunks_added": chunks_added,
            "file_size": len(content),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}",
        )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    repository_id: int = 1,  # Repository ID for multi-tenant isolation
    rag_service: RAGService = Depends(get_rag_service),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a document from the knowledge base

    Deletes both the vector embeddings and the database entry.

    Args:
        document_id: Knowledge entry ID
        repository_id: Repository ID for multi-tenant isolation
    """
    # Get knowledge entry
    result = await db.execute(
        select(KnowledgeEntry).where(KnowledgeEntry.id == document_id)
    )
    knowledge_entry = result.scalar_one_or_none()

    if not knowledge_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    try:
        # Delete from vector database (uses injected service with correct repository_id)
        if knowledge_entry.source_file:
            await rag_service.delete_by_source(knowledge_entry.source_file)

        # Delete from database
        await db.delete(knowledge_entry)
        await db.commit()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}",
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_knowledge_statistics(
    repository_id: int = 1,  # Repository ID for multi-tenant isolation
    rag_service: RAGService = Depends(get_rag_service),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get knowledge base statistics

    Provides statistics from both the vector database (PostgresBackend)
    and the relational database.

    Args:
        repository_id: Repository ID for multi-tenant isolation

    Returns:
        Statistics about the knowledge base including chunk counts,
        categories, and backend information
    """
    try:
        # Get RAG statistics (uses injected service with correct repository_id)
        rag_stats = await rag_service.get_statistics()

        # Get database statistics
        db_count_query = select(func.count()).select_from(KnowledgeEntry)
        db_result = await db.execute(db_count_query)
        db_total = db_result.scalar()

        # Get category breakdown from database
        category_query = select(
            KnowledgeEntry.category, func.count(KnowledgeEntry.id).label("count")
        ).group_by(KnowledgeEntry.category)

        category_result = await db.execute(category_query)
        db_categories = {row[0]: row[1] for row in category_result}

        return {
            "repository_id": repository_id,
            "collection": rag_stats["collection_name"],
            "vector_db": rag_stats,
            "database": {"total_entries": db_total, "categories": db_categories},
            "embedding_model": settings.EMBEDDING_MODEL,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting statistics: {str(e)}",
        )


@router.get("/collections", response_model=List[str])
async def list_collections(db: AsyncSession = Depends(get_db)) -> List[str]:
    """
    List available knowledge base collections

    Each repository has its own collection in the format: commandcenter_{repo_id}

    Returns:
        List of collection names (based on repositories)
    """
    try:
        # Query distinct repositories that have knowledge entries
        # This could be enhanced to query the actual PostgresBackend collections
        from app.models.repository import Repository

        result = await db.execute(select(Repository.id, Repository.name))
        repositories = result.all()

        return [f"commandcenter_{repo_id}" for repo_id, _ in repositories]

    except Exception:
        # Fallback to default
        return ["commandcenter_1"]


@router.get("/categories", response_model=List[str])
async def list_categories(
    repository_id: int = 1,  # Repository ID for multi-tenant isolation
    rag_service: RAGService = Depends(get_rag_service),
) -> List[str]:
    """
    List all categories in the knowledge base

    Note: Category listing from PostgresBackend is not yet implemented.
    This is a placeholder that will return empty list until enhanced.

    Args:
        repository_id: Repository ID for multi-tenant isolation

    Returns:
        List of category names
    """
    try:
        # Get categories from RAG service (uses injected service with correct repository_id)
        # Note: This currently returns empty list - needs custom SQL query implementation
        categories = await rag_service.get_categories()
        return categories

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting categories: {str(e)}",
        )
