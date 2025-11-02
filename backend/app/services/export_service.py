"""
ExportService - Service for exporting data to various formats.
"""

import json
import csv
from io import StringIO
from typing import List
from app.models.technology import Technology


class ExportService:
    """Service for exporting data to various formats."""

    def export_to_json(self, technologies: List[Technology]) -> str:
        """Export technologies to JSON.

        Args:
            technologies: List of Technology objects to export

        Returns:
            JSON string representation of the technologies

        Raises:
            ValueError: If technologies is None
        """
        if technologies is None:
            raise ValueError("Technologies cannot be None")

        data = [
            {
                "id": t.id,
                "title": t.title,
                "domain": t.domain,
                "status": t.status,
            }
            for t in technologies
        ]
        return json.dumps(data)

    def export_to_csv(self, technologies: List[Technology]) -> str:
        """Export technologies to CSV.

        Args:
            technologies: List of Technology objects to export

        Returns:
            CSV string representation of the technologies

        Raises:
            ValueError: If technologies is None
        """
        if technologies is None:
            raise ValueError("Technologies cannot be None")

        output = StringIO()
        if not technologies:
            return ""

        fieldnames = ["id", "title", "domain", "status"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for t in technologies:
            writer.writerow(
                {
                    "id": t.id,
                    "title": t.title,
                    "domain": t.domain,
                    "status": t.status,
                }
            )

        return output.getvalue()
