"""
Knowledge base and RAG endpoints
Provides access to document storage, retrieval, and semantic search
"""

from typing import List, Optional, Dict, Any
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import json

from app.database import get_db
from app.models.knowledge_entry import KnowledgeEntry
from app.schemas import (
    KnowledgeSearchRequest,
    KnowledgeSearchResult,
)
from app.services.rag_service import RAGService
from app.services.knowledgebeast_service import (
    KnowledgeBeastService,
    KNOWLEDGEBEAST_AVAILABLE,
)
from app.services.docling_service import DoclingService
from app.services.cache_service import CacheService
from app.config import settings

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# Dependency to get knowledge service (KnowledgeBeast or legacy RAG)
async def get_knowledge_service(
    project_id: int = 1,  # TODO: Get from auth context/header
    collection: str = "default",
):
    """Get knowledge service based on feature flag"""
    if settings.use_knowledgebeast and KNOWLEDGEBEAST_AVAILABLE:
        return KnowledgeBeastService(project_id=project_id)
    else:
        return RAGService(collection_name=collection)


# Legacy dependency (deprecated - use get_knowledge_service)
async def get_rag_service(collection_name: str = "default") -> RAGService:
    """Get RAG service instance with specified collection"""
    return RAGService(collection_name=collection_name)


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
    project_id: int = 1,  # TODO: Get from auth context
    collection: str = "default",
    mode: str = "hybrid",  # New: vector, keyword, or hybrid
    alpha: float = 0.7,  # New: hybrid blend (0=keyword, 1=vector)
    knowledge_service=Depends(get_knowledge_service),
    cache_service: CacheService = Depends(get_cache_service),
    db: AsyncSession = Depends(get_db),
) -> List[KnowledgeSearchResult]:
    """
    Query the knowledge base using semantic search

    Args:
        request: Search request with query, filters, and limit
        project_id: Project ID for isolation
        collection: Collection name (legacy compatibility)
        mode: Search mode - 'vector', 'keyword', or 'hybrid' (default: hybrid)
        alpha: Hybrid blend factor 0-1 (0=keyword only, 1=vector only)

    Returns:
        List of relevant knowledge entries with scores
    """
    # Create cache key (include mode and alpha for KB)
    cache_key = (
        f"kb_query:{project_id}:{mode}:{alpha}:{request.query}:{request.category}:{request.limit}"
    )

    # Try to get from cache first
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        return [KnowledgeSearchResult(**item) for item in json.loads(cached_result)]

    try:
        # Query using appropriate service
        if settings.use_knowledgebeast and KNOWLEDGEBEAST_AVAILABLE:
            # KnowledgeBeast supports mode and alpha parameters
            results = await knowledge_service.query(
                question=request.query,
                category=request.category,
                k=request.limit,
                mode=mode,
                alpha=alpha,
            )
        else:
            # Legacy RAG service doesn't support mode/alpha
            results = await knowledge_service.query(
                question=request.query,
                category=request.category,
                k=request.limit,
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
    "/documents",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
)
async def add_document(
    file: UploadFile = File(...),
    category: str = Form(...),
    technology_id: Optional[int] = Form(None),
    collection: str = Form("default"),
    rag_service: RAGService = Depends(get_rag_service),
    docling_service: DoclingService = Depends(get_docling_service),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Add a document to the knowledge base

    Supports PDF, Markdown, and text files via Docling processing

    Args:
        file: Uploaded file
        category: Document category
        technology_id: Optional technology association
        collection: Collection name for organization

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
            processed_content = await docling_service.process_markdown(content.decode("utf-8"))
        elif file_extension in ["txt", "text"]:
            processed_content = await docling_service.process_text(content.decode("utf-8"))
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

        # Reinitialize RAG service with correct collection
        rag_service = RAGService(collection_name=collection)

        # Add to vector database
        chunks_added = await rag_service.add_document(content=processed_content, metadata=metadata)

        # Create knowledge entry in database
        knowledge_entry = KnowledgeEntry(
            title=filename,
            content=processed_content[:1000],  # Store preview
            category=category,
            technology_id=technology_id,
            source_file=filename,
            source_type=file_extension,
            embedding_model=settings.embedding_model,
        )

        db.add(knowledge_entry)
        await db.commit()
        await db.refresh(knowledge_entry)

        return {
            "id": knowledge_entry.id,
            "filename": filename,
            "category": category,
            "collection": collection,
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
    collection: str = "default",
    rag_service: RAGService = Depends(get_rag_service),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a document from the knowledge base

    Args:
        document_id: Knowledge entry ID
        collection: Collection name
    """
    # Get knowledge entry
    result = await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.id == document_id))
    knowledge_entry = result.scalar_one_or_none()

    if not knowledge_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    try:
        # Reinitialize RAG service with correct collection
        rag_service = RAGService(collection_name=collection)

        # Delete from vector database
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
    collection: str = "default",
    rag_service: RAGService = Depends(get_rag_service),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get knowledge base statistics

    Args:
        collection: Collection name

    Returns:
        Statistics about the knowledge base
    """
    try:
        # Reinitialize RAG service with correct collection
        rag_service = RAGService(collection_name=collection)

        # Get RAG statistics
        rag_stats = await rag_service.get_statistics()

        # Get database statistics
        db_count_query = select(func.count()).select_from(KnowledgeEntry)
        db_result = await db.execute(db_count_query)
        db_total = db_result.scalar()

        # Get category breakdown from database
        category_query = select(
            KnowledgeEntry.category,
            func.count(KnowledgeEntry.id).label("count"),
        ).group_by(KnowledgeEntry.category)

        category_result = await db.execute(category_query)
        db_categories = {row[0]: row[1] for row in category_result}

        return {
            "collection": collection,
            "vector_db": rag_stats,
            "database": {
                "total_entries": db_total,
                "categories": db_categories,
            },
            "embedding_model": settings.embedding_model,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting statistics: {str(e)}",
        )


@router.get("/collections", response_model=List[str])
async def list_collections() -> List[str]:
    """
    List available knowledge base collections

    Returns:
        List of collection names
    """
    # This would need to be implemented based on how collections are stored
    # For now, return a default list
    return ["default", "performia_docs", "research", "technical"]


@router.get("/categories", response_model=List[str])
async def list_categories(
    collection: str = "default",
    rag_service: RAGService = Depends(get_rag_service),
) -> List[str]:
    """
    List all categories in the knowledge base

    Args:
        collection: Collection name

    Returns:
        List of category names
    """
    try:
        # Reinitialize RAG service with correct collection
        rag_service = RAGService(collection_name=collection)

        categories = await rag_service.get_categories()
        return categories

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting categories: {str(e)}",
        )
