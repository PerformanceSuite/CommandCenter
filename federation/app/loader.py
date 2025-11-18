import yaml
from pathlib import Path
from pydantic import ValidationError
from app.services.catalog_service import CatalogService
from app.database import get_async_session
from app.schemas.config import ProjectsConfig
import logging

logger = logging.getLogger(__name__)


async def load_projects_from_yaml():
    """
    Load projects from config/projects.yaml and register them.

    Validates YAML structure with Pydantic schema before loading.
    Raises ValidationError if config is invalid.
    """
    config_path = Path(__file__).parent.parent / "config" / "projects.yaml"

    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return

    # Load and parse YAML
    try:
        with open(config_path) as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in {config_path}: {e}")
        raise ValueError(f"Failed to parse YAML config: {e}")

    # Validate with Pydantic schema
    try:
        config = ProjectsConfig(**raw_config)
        logger.info(f"Loaded {len(config.projects)} projects from config")
    except ValidationError as e:
        logger.error(f"Invalid project configuration in {config_path}:")
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            logger.error(f"  {field}: {error['msg']}")
        raise ValueError(f"Invalid projects.yaml configuration: {e}")

    # Register validated projects in catalog
    async with get_async_session() as db:
        service = CatalogService(db)

        for project in config.projects:
            await service.register_project(
                slug=project.slug,
                name=project.name,
                hub_url=project.hub_url,
                mesh_namespace=project.mesh_namespace,
                tags=project.tags
            )
            logger.info(f"Registered project: {project.slug}")
