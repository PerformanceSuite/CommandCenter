# Phase 1b: Database Isolation Agent

## Mission
Add project_id foreign key to ALL tables and implement complete database isolation.

## Priority
CRITICAL - Blocks multi-project deployment

## Estimated Time
12 hours

## Tasks

### 1. Create Project Model (2 hours)
```python
# backend/app/models/project.py
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (UniqueConstraint('owner', 'name'),)
```

### 2. Add project_id to All Tables (4 hours)
Tables to update:
- repositories
- technologies
- research_tasks
- knowledge_entries
- webhooks
- webhook_events
- rate_limits

For each table, add:
```python
project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
project = relationship("Project", back_populates="[table_name]")
```

### 3. Create Alembic Migration (2 hours)
```bash
cd backend
alembic revision --autogenerate -m "add project_id to all tables"
```

Migration must:
- Create projects table
- Add project_id columns to all tables
- Create foreign key constraints
- Add indexes on project_id
- Create default project for existing data
- Assign existing data to default project

### 4. Update All Queries (3 hours)
Update every SQLAlchemy query to include:
```python
.filter(Model.project_id == project_id)
```

Files to update:
- All routers in `backend/app/routers/`
- All services in `backend/app/services/`
- All repositories (if using repository pattern)

### 5. Add Validation (1 hour)
- Validate project_id exists
- Validate user has access to project
- Add error handling for invalid project_id

## Success Criteria
- ✅ Projects table created
- ✅ All tables have project_id foreign key
- ✅ Migration runs successfully
- ✅ All queries filtered by project_id
- ✅ Existing data migrated to default project
- ✅ Tests pass
- ✅ No cross-project data access possible
