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


# Dependency to get RAG service
async def get_rag_service(repository_id: Optional[int] = None) -> RAGService:
    """Get RAG service instance with specified repository collection"""
    return RAGService(repository_id=repository_id)


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
    repository_id: Optional[int] = None,
    cache_service: CacheService = Depends(get_cache_service),
    db: AsyncSession = Depends(get_db),
) -> List[KnowledgeSearchResult]:
    """
    Query the knowledge base using semantic search

    IMPORTANT: Queries are isolated per repository when repository_id is provided.
    This prevents Repository A's queries from returning Repository B's documents.

    Args:
        request: Search request with query, filters, and limit
        repository_id: Repository ID for isolated search (optional)

    Returns:
        List of relevant knowledge entries with scores
    """
    # Create cache key from query parameters
    cache_key = f"rag_query:{repository_id}:{request.query}:{request.category}:{request.technology_id}:{request.limit}"

    # Try to get from cache first
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        return [KnowledgeSearchResult(**item) for item in json.loads(cached_result)]

    try:
        # Initialize RAG service with repository-specific collection
        rag_service = RAGService(repository_id=repository_id)

        # Query the vector database (repository-isolated)
        results = await rag_service.query(
            question=request.query,
            category=request.category,
            k=request.limit,
            repository_id=repository_id,
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
    repository_id: Optional[int] = Form(None),
    docling_service: DoclingService = Depends(get_docling_service),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Add a document to the repository's knowledge base collection

    Supports PDF, Markdown, and text files via Docling processing

    Args:
        file: Uploaded file
        category: Document category
        technology_id: Optional technology association
        repository_id: Repository ID for collection isolation (optional)

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

        # Initialize RAG service with repository-specific collection
        rag_service = RAGService(repository_id=repository_id)

        # Add to vector database (repository-isolated)
        result = await rag_service.add_document(
            content=processed_content, metadata=metadata, repository_id=repository_id
        )

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
            "repository_id": repository_id,
            "collection": result["collection"],
            "chunks_added": result["chunks_added"],
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
    repository_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a document from the repository's knowledge base collection

    Args:
        document_id: Knowledge entry ID
        repository_id: Repository ID for collection isolation (optional)
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
        # Initialize RAG service with repository-specific collection
        rag_service = RAGService(repository_id=repository_id)

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
    repository_id: Optional[int] = None, db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get knowledge base statistics for repository's collection

    Args:
        repository_id: Repository ID for collection isolation (optional)

    Returns:
        Statistics about the repository's knowledge base
    """
    try:
        # Initialize RAG service with repository-specific collection
        rag_service = RAGService(repository_id=repository_id)

        # Get RAG statistics
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
            "collection": rag_stats.get("collection_name"),
            "vector_db": rag_stats,
            "database": {"total_entries": db_total, "categories": db_categories},
            "embedding_model": settings.embedding_model,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting statistics: {str(e)}",
        )


@router.get("/collections", response_model=List[Dict[str, Any]])
async def list_collections() -> List[Dict[str, Any]]:
    """
    List all ChromaDB collections

    Returns:
        List of collection information including document counts
    """
    try:
        rag_service = RAGService()
        collections = await rag_service.list_all_collections()
        return collections
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing collections: {str(e)}",
        )


@router.get("/collections/{repository_id}/stats", response_model=Dict[str, Any])
async def get_collection_stats(repository_id: int) -> Dict[str, Any]:
    """
    Get statistics for a specific repository's collection

    Args:
        repository_id: Repository ID

    Returns:
        Collection statistics
    """
    try:
        rag_service = RAGService()
        stats = await rag_service.get_collection_stats(repository_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting collection stats: {str(e)}",
        )


@router.delete("/collections/{repository_id}", status_code=status.HTTP_200_OK)
async def delete_repository_collection(repository_id: int) -> Dict[str, Any]:
    """
    Delete entire knowledge base collection for repository

    WARNING: This is a destructive operation and cannot be undone.
    Use when a repository is deleted.

    Args:
        repository_id: Repository ID

    Returns:
        Deletion status
    """
    try:
        rag_service = RAGService()
        result = await rag_service.delete_collection(repository_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting collection: {str(e)}",
        )


@router.get("/categories", response_model=List[str])
async def list_categories(repository_id: Optional[int] = None) -> List[str]:
    """
    List all categories in the repository's knowledge base

    Args:
        repository_id: Repository ID for collection isolation (optional)

    Returns:
        List of category names
    """
    try:
        # Initialize RAG service with repository-specific collection
        rag_service = RAGService(repository_id=repository_id)

        categories = await rag_service.get_categories()
        return categories

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting categories: {str(e)}",
        )
