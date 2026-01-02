"""
Integration tests for Document Intelligence ingest endpoint.

Tests the POST /api/v1/graph/document-intelligence/ingest endpoint
and underlying GraphService.ingest_document_intelligence() method.
"""

import pytest
from sqlalchemy import select

from app.models.graph import GraphConcept, GraphDocument, GraphLink, GraphRequirement, LinkType
from app.schemas.graph import (
    CreateConceptRequest,
    CreateDocumentRequest,
    CreateRequirementRequest,
    IngestDocumentIntelligenceRequest,
)
from app.services.graph_service import GraphService

# ============================================================================
# Service-Level Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ingest_empty_request(db_session):
    """Test ingestion with empty request returns zero counts."""
    service = GraphService(db_session)

    request = IngestDocumentIntelligenceRequest(
        documents=[],
        concepts=[],
        requirements=[],
    )

    response = await service.ingest_document_intelligence(
        project_id=1,
        request=request,
    )

    assert response.documents_created == 0
    assert response.documents_updated == 0
    assert response.concepts_created == 0
    assert response.concepts_updated == 0
    assert response.requirements_created == 0
    assert response.requirements_updated == 0
    assert response.links_created == 0
    assert len(response.errors) == 0
    assert "processing_time_ms" in response.metadata


@pytest.mark.asyncio
async def test_ingest_documents_only(db_session):
    """Test ingestion of documents without concepts or requirements."""
    service = GraphService(db_session)

    request = IngestDocumentIntelligenceRequest(
        documents=[
            CreateDocumentRequest(
                path="docs/test/doc1.md",
                title="Test Document 1",
                doc_type="plan",
                status="active",
                word_count=100,
            ),
            CreateDocumentRequest(
                path="docs/test/doc2.md",
                title="Test Document 2",
                doc_type="guide",
                status="active",
                audience="developers",
                word_count=200,
            ),
        ],
        concepts=[],
        requirements=[],
    )

    response = await service.ingest_document_intelligence(
        project_id=1,
        request=request,
    )

    assert response.documents_created == 2
    assert response.documents_updated == 0
    assert len(response.errors) == 0

    # Verify documents were created in database
    stmt = select(GraphDocument).filter(GraphDocument.project_id == 1)
    result = await db_session.execute(stmt)
    documents = result.scalars().all()

    assert len(documents) == 2
    paths = {doc.path for doc in documents}
    assert "docs/test/doc1.md" in paths
    assert "docs/test/doc2.md" in paths


@pytest.mark.asyncio
async def test_ingest_document_upsert(db_session):
    """Test that documents are updated on re-ingestion by path."""
    service = GraphService(db_session)

    # First ingestion - create
    request1 = IngestDocumentIntelligenceRequest(
        documents=[
            CreateDocumentRequest(
                path="docs/upsert-test.md",
                title="Original Title",
                doc_type="plan",
                status="active",
                word_count=100,
            ),
        ],
    )

    response1 = await service.ingest_document_intelligence(project_id=1, request=request1)
    assert response1.documents_created == 1
    assert response1.documents_updated == 0

    # Second ingestion - update same path
    request2 = IngestDocumentIntelligenceRequest(
        documents=[
            CreateDocumentRequest(
                path="docs/upsert-test.md",
                title="Updated Title",
                doc_type="guide",  # Changed type
                status="completed",  # Changed status
                word_count=200,
            ),
        ],
    )

    response2 = await service.ingest_document_intelligence(project_id=1, request=request2)
    assert response2.documents_created == 0
    assert response2.documents_updated == 1

    # Verify the update
    stmt = select(GraphDocument).filter(
        GraphDocument.project_id == 1,
        GraphDocument.path == "docs/upsert-test.md",
    )
    result = await db_session.execute(stmt)
    doc = result.scalar_one()

    assert doc.title == "Updated Title"
    assert doc.doc_type.value == "guide"
    assert doc.status.value == "completed"
    assert doc.word_count == 200


@pytest.mark.asyncio
async def test_ingest_concepts_only(db_session):
    """Test ingestion of concepts without documents or requirements."""
    service = GraphService(db_session)

    request = IngestDocumentIntelligenceRequest(
        concepts=[
            CreateConceptRequest(
                name="TestConcept1",
                concept_type="product",
                definition="A test product concept",
                confidence="high",
            ),
            CreateConceptRequest(
                name="TestConcept2",
                concept_type="feature",
                definition="A test feature concept",
                domain="testing",
                confidence="medium",
            ),
        ],
    )

    response = await service.ingest_document_intelligence(project_id=1, request=request)

    assert response.concepts_created == 2
    assert response.concepts_updated == 0
    assert len(response.errors) == 0

    # Verify concepts in database
    stmt = select(GraphConcept).filter(GraphConcept.project_id == 1)
    result = await db_session.execute(stmt)
    concepts = result.scalars().all()

    assert len(concepts) == 2
    names = {c.name for c in concepts}
    assert "TestConcept1" in names
    assert "TestConcept2" in names


@pytest.mark.asyncio
async def test_ingest_concept_upsert(db_session):
    """Test that concepts are updated on re-ingestion by name."""
    service = GraphService(db_session)

    # First ingestion
    request1 = IngestDocumentIntelligenceRequest(
        concepts=[
            CreateConceptRequest(
                name="UpsertConcept",
                concept_type="product",
                definition="Original definition",
                confidence="medium",
            ),
        ],
    )

    response1 = await service.ingest_document_intelligence(project_id=1, request=request1)
    assert response1.concepts_created == 1

    # Second ingestion - update
    request2 = IngestDocumentIntelligenceRequest(
        concepts=[
            CreateConceptRequest(
                name="UpsertConcept",
                concept_type="feature",  # Changed
                definition="Updated definition",
                confidence="high",  # Changed
            ),
        ],
    )

    response2 = await service.ingest_document_intelligence(project_id=1, request=request2)
    assert response2.concepts_created == 0
    assert response2.concepts_updated == 1

    # Verify update
    stmt = select(GraphConcept).filter(
        GraphConcept.project_id == 1,
        GraphConcept.name == "UpsertConcept",
    )
    result = await db_session.execute(stmt)
    concept = result.scalar_one()

    assert concept.definition == "Updated definition"
    assert concept.concept_type.value == "feature"
    assert concept.confidence.value == "high"


@pytest.mark.asyncio
async def test_ingest_requirements_only(db_session):
    """Test ingestion of requirements without documents or concepts."""
    service = GraphService(db_session)

    request = IngestDocumentIntelligenceRequest(
        requirements=[
            CreateRequirementRequest(
                req_id="REQ-001",
                text="System MUST support user authentication",
                req_type="functional",
                priority="critical",
                status="accepted",
            ),
            CreateRequirementRequest(
                req_id="REQ-002",
                text="System SHOULD respond within 200ms",
                req_type="nonFunctional",
                priority="high",
                status="proposed",
            ),
        ],
    )

    response = await service.ingest_document_intelligence(project_id=1, request=request)

    assert response.requirements_created == 2
    assert response.requirements_updated == 0
    assert len(response.errors) == 0

    # Verify requirements in database
    stmt = select(GraphRequirement).filter(GraphRequirement.project_id == 1)
    result = await db_session.execute(stmt)
    requirements = result.scalars().all()

    assert len(requirements) == 2
    req_ids = {r.req_id for r in requirements}
    assert "REQ-001" in req_ids
    assert "REQ-002" in req_ids


@pytest.mark.asyncio
async def test_ingest_requirement_upsert(db_session):
    """Test that requirements are updated on re-ingestion by req_id."""
    service = GraphService(db_session)

    # First ingestion
    request1 = IngestDocumentIntelligenceRequest(
        requirements=[
            CreateRequirementRequest(
                req_id="REQ-UPSERT",
                text="Original requirement text",
                req_type="functional",
                priority="medium",
                status="proposed",
            ),
        ],
    )

    response1 = await service.ingest_document_intelligence(project_id=1, request=request1)
    assert response1.requirements_created == 1

    # Second ingestion - update
    request2 = IngestDocumentIntelligenceRequest(
        requirements=[
            CreateRequirementRequest(
                req_id="REQ-UPSERT",
                text="Updated requirement text",
                req_type="nonFunctional",  # Changed
                priority="critical",  # Changed
                status="accepted",  # Changed
            ),
        ],
    )

    response2 = await service.ingest_document_intelligence(project_id=1, request=request2)
    assert response2.requirements_created == 0
    assert response2.requirements_updated == 1

    # Verify update
    stmt = select(GraphRequirement).filter(
        GraphRequirement.project_id == 1,
        GraphRequirement.req_id == "REQ-UPSERT",
    )
    result = await db_session.execute(stmt)
    req = result.scalar_one()

    assert req.text == "Updated requirement text"
    assert req.req_type.value == "nonFunctional"
    assert req.priority.value == "critical"
    assert req.status.value == "accepted"


@pytest.mark.asyncio
async def test_ingest_with_links(db_session):
    """Test that links are created between documents and extracted entities."""
    service = GraphService(db_session)

    # First create a document to get its ID
    doc_request = IngestDocumentIntelligenceRequest(
        documents=[
            CreateDocumentRequest(
                path="docs/source-doc.md",
                title="Source Document",
                doc_type="plan",
                status="active",
                word_count=500,
            ),
        ],
    )
    doc_response = await service.ingest_document_intelligence(project_id=1, request=doc_request)
    assert doc_response.documents_created == 1

    # Get the document ID
    stmt = select(GraphDocument).filter(
        GraphDocument.project_id == 1,
        GraphDocument.path == "docs/source-doc.md",
    )
    result = await db_session.execute(stmt)
    doc = result.scalar_one()
    doc_id = doc.id

    # Now create concepts and requirements linked to the document
    linked_request = IngestDocumentIntelligenceRequest(
        concepts=[
            CreateConceptRequest(
                name="LinkedConcept",
                concept_type="feature",
                definition="A concept extracted from source doc",
                source_document_id=doc_id,
                confidence="high",
            ),
        ],
        requirements=[
            CreateRequirementRequest(
                req_id="REQ-LINKED",
                text="A requirement from the source document",
                req_type="functional",
                priority="high",
                source_document_id=doc_id,
            ),
        ],
    )

    linked_response = await service.ingest_document_intelligence(
        project_id=1, request=linked_request
    )

    assert linked_response.concepts_created == 1
    assert linked_response.requirements_created == 1
    assert linked_response.links_created == 2  # One for concept, one for requirement

    # Verify links were created
    stmt = select(GraphLink).filter(
        GraphLink.from_entity == "graph_documents",
        GraphLink.from_id == doc_id,
        GraphLink.type == LinkType.EXTRACTS_FROM,
    )
    result = await db_session.execute(stmt)
    links = result.scalars().all()

    assert len(links) == 2
    to_entities = {link.to_entity for link in links}
    assert "graph_concepts" in to_entities
    assert "graph_requirements" in to_entities


@pytest.mark.asyncio
async def test_ingest_full_pipeline(db_session):
    """Test full Document Intelligence pipeline with all entity types."""
    service = GraphService(db_session)

    request = IngestDocumentIntelligenceRequest(
        documents=[
            CreateDocumentRequest(
                path="docs/sprint-plan.md",
                title="Sprint 6 Planning Document",
                doc_type="plan",
                subtype="sprint-plan",
                status="active",
                audience="engineering",
                value_assessment="high",
                word_count=1500,
            ),
            CreateDocumentRequest(
                path="docs/api-guide.md",
                title="API Integration Guide",
                doc_type="guide",
                status="active",
                word_count=800,
            ),
        ],
        concepts=[
            CreateConceptRequest(
                name="Document Intelligence",
                concept_type="feature",
                definition="Multi-agent system for document analysis",
                domain="ai-agents",
                confidence="high",
                related_entities=["KnowledgeBeast", "Graph Service"],
            ),
            CreateConceptRequest(
                name="KnowledgeBeast",
                concept_type="product",
                definition="RAG engine for knowledge retrieval",
                domain="knowledge-management",
                confidence="high",
            ),
        ],
        requirements=[
            CreateRequirementRequest(
                req_id="REQ-DI-001",
                text="System MUST process documents through configurable pipeline",
                req_type="functional",
                priority="critical",
                status="accepted",
                source_concept="Document Intelligence",
            ),
            CreateRequirementRequest(
                req_id="REQ-DI-002",
                text="Pipeline SHOULD support parallel execution",
                req_type="nonFunctional",
                priority="high",
                status="proposed",
            ),
        ],
    )

    response = await service.ingest_document_intelligence(project_id=1, request=request)

    assert response.documents_created == 2
    assert response.concepts_created == 2
    assert response.requirements_created == 2
    assert len(response.errors) == 0
    assert response.metadata["documents_processed"] == 2
    assert response.metadata["concepts_processed"] == 2
    assert response.metadata["requirements_processed"] == 2

    print(f"✅ Full pipeline test: {response.metadata}")


@pytest.mark.asyncio
async def test_ingest_multi_tenant_isolation(db_session):
    """Test that ingestion respects project boundaries."""
    service = GraphService(db_session)

    # Ingest to project 1
    request1 = IngestDocumentIntelligenceRequest(
        documents=[
            CreateDocumentRequest(
                path="docs/project1.md",
                title="Project 1 Doc",
                doc_type="plan",
                status="active",
                word_count=100,
            ),
        ],
    )
    await service.ingest_document_intelligence(project_id=1, request=request1)

    # Ingest to project 2
    request2 = IngestDocumentIntelligenceRequest(
        documents=[
            CreateDocumentRequest(
                path="docs/project2.md",
                title="Project 2 Doc",
                doc_type="guide",
                status="active",
                word_count=200,
            ),
        ],
    )
    await service.ingest_document_intelligence(project_id=2, request=request2)

    # Verify isolation - project 1 should only see its doc
    stmt1 = select(GraphDocument).filter(GraphDocument.project_id == 1)
    result1 = await db_session.execute(stmt1)
    docs1 = result1.scalars().all()

    stmt2 = select(GraphDocument).filter(GraphDocument.project_id == 2)
    result2 = await db_session.execute(stmt2)
    docs2 = result2.scalars().all()

    assert len(docs1) == 1
    assert docs1[0].path == "docs/project1.md"

    assert len(docs2) == 1
    assert docs2[0].path == "docs/project2.md"


# ============================================================================
# API Endpoint Tests
# ============================================================================


@pytest.mark.asyncio
async def test_api_ingest_endpoint_success(api_client):
    """Test the API endpoint returns 201 and correct response."""
    response = await api_client.post(
        "/graph/document-intelligence/ingest",
        json={
            "documents": [
                {
                    "path": "docs/api-test.md",
                    "title": "API Test Document",
                    "doc_type": "plan",
                    "status": "active",
                    "word_count": 100,
                }
            ],
            "concepts": [
                {
                    "name": "API Test Concept",
                    "concept_type": "feature",
                    "definition": "Test concept via API",
                    "confidence": "high",
                }
            ],
            "requirements": [
                {
                    "req_id": "REQ-API-001",
                    "text": "API test requirement",
                    "req_type": "functional",
                    "priority": "medium",
                }
            ],
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["documents_created"] == 1
    assert data["concepts_created"] == 1
    assert data["requirements_created"] == 1
    assert "processing_time_ms" in data["metadata"]


@pytest.mark.asyncio
async def test_api_ingest_empty_request(api_client):
    """Test API accepts empty request."""
    response = await api_client.post(
        "/graph/document-intelligence/ingest",
        json={
            "documents": [],
            "concepts": [],
            "requirements": [],
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["documents_created"] == 0
    assert data["concepts_created"] == 0
    assert data["requirements_created"] == 0


@pytest.mark.asyncio
async def test_api_ingest_unauthenticated(unauthenticated_api_client):
    """Test that unauthenticated requests are rejected."""
    response = await unauthenticated_api_client.post(
        "/graph/document-intelligence/ingest",
        json={"documents": [], "concepts": [], "requirements": []},
    )

    # Should get 401 or 403
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_api_ingest_invalid_doc_type(api_client):
    """Test API validates document type enum."""
    response = await api_client.post(
        "/graph/document-intelligence/ingest",
        json={
            "documents": [
                {
                    "path": "docs/invalid.md",
                    "doc_type": "invalid_type",  # Invalid enum value
                    "status": "active",
                }
            ],
        },
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_api_ingest_invalid_req_id_format(api_client):
    """Test API validates requirement ID format."""
    response = await api_client.post(
        "/graph/document-intelligence/ingest",
        json={
            "requirements": [
                {
                    "req_id": "INVALID",  # Should match REQ-XXX pattern
                    "text": "Test requirement",
                    "req_type": "functional",
                }
            ],
        },
    )

    assert response.status_code == 422  # Validation error
