import yaml
from pathlib import Path
from app.services.catalog_service import CatalogService
from app.database import get_async_session
import logging

logger = logging.getLogger(__name__)


async def load_projects_from_yaml():
    """Load projects from config/projects.yaml and register them."""
    config_path = Path(__file__).parent.parent / "config" / "projects.yaml"

    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return

    with open(config_path) as f:
        config = yaml.safe_load(f)

    async with get_async_session() as db:
        service = CatalogService(db)

        for project_data in config.get("projects", []):
            await service.register_project(
                slug=project_data["slug"],
                name=project_data["name"],
                hub_url=project_data["hub_url"],
                mesh_namespace=project_data["mesh_namespace"],
                tags=project_data.get("tags", [])
            )
            logger.info(f"Registered project: {project_data['slug']}")
