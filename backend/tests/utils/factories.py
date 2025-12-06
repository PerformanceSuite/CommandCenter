"""
Factory classes for creating test data
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import get_password_hash
from app.models.knowledge_entry import KnowledgeEntry
from app.models.project import Project
from app.models.repository import Repository
from app.models.technology import Technology, TechnologyDomain, TechnologyStatus
from app.models.user import User


class UserFactory:
    """Factory for creating test users"""

    @staticmethod
    async def create(
        db: AsyncSession,
        email: str = "test@example.com",
        password: str = "testpassword123",
        full_name: Optional[str] = "Test User",
        is_active: bool = True,
        is_superuser: bool = False,
    ) -> User:
        """Create a test user"""
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            is_active=is_active,
            is_superuser=is_superuser,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


class ProjectFactory:
    """Factory for creating test projects"""

    @staticmethod
    async def create(
        db: AsyncSession,
        name: str = "Test Project",
        owner: str = "testowner",
        description: Optional[str] = "A test project for testing",
    ) -> Project:
        """Create a test project"""
        project = Project(
            name=name,
            owner=owner,
            description=description,
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project


class TechnologyFactory:
    """Factory for creating test technologies"""

    @staticmethod
    async def create(
        db: AsyncSession,
        project_id: int,
        title: str = "Python",
        vendor: Optional[str] = None,
        domain: TechnologyDomain = TechnologyDomain.OTHER,
        status: TechnologyStatus = TechnologyStatus.DISCOVERY,
        relevance_score: int = 50,
        priority: int = 3,
        description: Optional[str] = "A high-level programming language",
        notes: Optional[str] = None,
        use_cases: Optional[str] = None,
        documentation_url: Optional[str] = None,
        repository_url: Optional[str] = None,
        website_url: Optional[str] = None,
        tags: Optional[str] = None,
        **kwargs,
    ) -> Technology:
        """Create a test technology"""
        technology = Technology(
            project_id=project_id,
            title=title,
            vendor=vendor,
            domain=domain,
            status=status,
            relevance_score=relevance_score,
            priority=priority,
            description=description,
            notes=notes,
            use_cases=use_cases,
            documentation_url=documentation_url,
            repository_url=repository_url,
            website_url=website_url,
            tags=tags,
            **kwargs,
        )
        db.add(technology)
        await db.commit()
        await db.refresh(technology)
        return technology


class RepositoryFactory:
    """Factory for creating test repositories"""

    @staticmethod
    async def create(
        db: AsyncSession,
        project_id: int,
        owner: str = "testowner",
        name: str = "testrepo",
        full_name: Optional[str] = None,
        description: Optional[str] = "A test repository",
        url: Optional[str] = None,
        clone_url: Optional[str] = None,
        default_branch: str = "main",
        is_private: bool = False,
        github_id: Optional[int] = None,
        access_token: Optional[str] = None,
        language: Optional[str] = "Python",
        stars: int = 0,
        forks: int = 0,
    ) -> Repository:
        """Create a test repository"""
        if full_name is None:
            full_name = f"{owner}/{name}"
        if url is None:
            url = f"https://github.com/{owner}/{name}"
        if clone_url is None:
            clone_url = f"https://github.com/{owner}/{name}.git"
        if github_id is None:
            github_id = hash(full_name) % 1000000

        repository = Repository(
            project_id=project_id,
            owner=owner,
            name=name,
            full_name=full_name,
            description=description,
            url=url,
            clone_url=clone_url,
            default_branch=default_branch,
            is_private=is_private,
            github_id=github_id,
            language=language,
            stars=stars,
            forks=forks,
        )

        # Set access token if provided (will be encrypted)
        if access_token:
            repository.access_token = access_token

        db.add(repository)
        await db.commit()
        await db.refresh(repository)
        return repository


class KnowledgeEntryFactory:
    """Factory for creating test knowledge entries"""

    @staticmethod
    async def create(
        db: AsyncSession,
        project_id: int,
        title: str = "Test Knowledge Entry",
        content: str = "Test content for the knowledge entry",
        category: str = "documentation",
        technology_id: Optional[int] = None,
        source_file: Optional[str] = None,
        source_url: Optional[str] = None,
        source_type: Optional[str] = None,
        vector_db_id: Optional[str] = None,
        embedding_model: Optional[str] = None,
        page_number: Optional[int] = None,
        chunk_index: Optional[int] = None,
        confidence_score: Optional[float] = None,
        relevance_score: Optional[float] = None,
    ) -> KnowledgeEntry:
        """Create a test knowledge entry"""
        entry = KnowledgeEntry(
            project_id=project_id,
            title=title,
            content=content,
            category=category,
            technology_id=technology_id,
            source_file=source_file,
            source_url=source_url,
            source_type=source_type,
            vector_db_id=vector_db_id,
            embedding_model=embedding_model,
            page_number=page_number,
            chunk_index=chunk_index,
            confidence_score=confidence_score,
            relevance_score=relevance_score,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry
