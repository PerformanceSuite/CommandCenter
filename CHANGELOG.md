# Changelog

All notable changes to CommandCenter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **KnowledgeBeast Migration to Monorepo**: Migrated from external PyPI dependency to vendored package in `libs/knowledgebeast/`
  - Added KnowledgeBeast v3.0-final-standalone as monorepo library
  - Updated `backend/requirements.txt` to use editable install: `-e ../libs/knowledgebeast`
  - Upgraded dependencies for compatibility:
    - `docling` from `>=1.0.0,<2.0.0` to `>=2.5.5`
    - `openpyxl` from `==3.1.2` to `>=3.1.5,<4.0.0`
  - Maintained PostgreSQL + pgvector backend for RAG functionality
  - No API changes - fully backward compatible

### Added
- Monorepo structure with `libs/` directory for vendored packages
- KnowledgeBeast package at `libs/knowledgebeast/` (79 files, 24k+ lines)
- Updated `.gitignore` for monorepo library exclusions

### Documentation
- Updated README.md to reflect KnowledgeBeast + pgvector (removed ChromaDB references)
- Updated CLAUDE.md with monorepo package information
- Updated PROJECT.md with migration status
- Added this CHANGELOG.md for version tracking

## [0.1.0] - 2025-10-27

### Initial Release
- Multi-project R&D management and knowledge base system
- Technology tracking and visualization (Tech Radar)
- Research task management
- RAG-powered knowledge base with KnowledgeBeast + PostgreSQL/pgvector
- GitHub repository integration and sync
- FastAPI backend with React/TypeScript frontend
- Docker Compose deployment
- Data isolation architecture for multi-instance deployments
