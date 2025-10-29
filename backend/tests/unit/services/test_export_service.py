"""Unit tests for ExportService."""
import pytest
import json
import csv
from io import StringIO
from app.services.export_service import ExportService
from app.models.technology import Technology


@pytest.fixture
def sample_technologies():
    """Sample technologies for export testing."""
    return [
        Technology(id=1, title="Python", domain="backend", status="adopt"),
        Technology(id=2, title="React", domain="frontend", status="trial"),
    ]


@pytest.mark.unit
class TestExportService:
    """Test ExportService class"""

    def test_export_to_json(self, sample_technologies):
        """ExportService exports to JSON format."""
        service = ExportService()
        result = service.export_to_json(sample_technologies)

        data = json.loads(result)
        assert len(data) == 2
        assert data[0]["title"] == "Python"
        assert data[1]["title"] == "React"

    def test_export_to_csv(self, sample_technologies):
        """ExportService exports to CSV format."""
        service = ExportService()
        result = service.export_to_csv(sample_technologies)

        reader = csv.DictReader(StringIO(result))
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["title"] == "Python"
        assert rows[1]["domain"] == "frontend"

    def test_export_error_handling(self):
        """ExportService handles errors gracefully."""
        service = ExportService()

        # Empty list should return empty JSON array
        result = service.export_to_json([])
        assert result == "[]"

        # None should raise ValueError
        with pytest.raises(ValueError):
            service.export_to_json(None)
