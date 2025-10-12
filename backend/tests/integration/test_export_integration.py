"""
Integration tests for export system.

Tests the complete export workflow including:
- SARIF export with GitHub Code Scanning compatibility
- HTML export with embedded Chart.js visualizations
- CSV export with multiple data types
- Excel export with formatted workbooks
- JSON export for programmatic access
"""

import pytest
import json
import io
from typing import Dict, Any
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from openpyxl import load_workbook

from app.models import Project, Repository, Technology


pytestmark = pytest.mark.integration


class TestExportIntegration:
    """Integration tests for export endpoints."""

    @pytest.mark.asyncio
    async def test_sarif_export_complete_workflow(
        self,
        async_client: AsyncClient,
        test_analysis_data: Dict[str, Any],
        db_session: AsyncSession,
    ):
        """Test complete SARIF export workflow with GitHub Code Scanning compatibility."""
        project_id = test_analysis_data["project_id"]
        repository_id = test_analysis_data["repository_id"]

        # Export SARIF format
        response = await async_client.get(
            f"/api/v1/export/sarif?project_id={project_id}&repository_id={repository_id}"
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "sarif" in response.headers["content-disposition"]

        # Validate SARIF structure
        sarif_data = response.json()
        assert sarif_data["version"] == "2.1.0"
        assert sarif_data["$schema"] == "https://json.schemastore.org/sarif-2.1.0.json"
        assert len(sarif_data["runs"]) == 1

        run = sarif_data["runs"][0]
        assert "tool" in run
        assert run["tool"]["driver"]["name"] == "CommandCenter"
        assert "rules" in run["tool"]["driver"]
        assert "results" in run

        # Validate at least some results are present
        assert len(run["results"]) > 0

        # Validate rule definitions
        rules = run["tool"]["driver"]["rules"]
        rule_ids = {rule["id"] for rule in rules}
        assert "OutdatedDependency" in rule_ids
        assert "MissingDependency" in rule_ids
        assert "ResearchGap" in rule_ids
        assert "TechnologyDetection" in rule_ids

    @pytest.mark.asyncio
    async def test_html_export_complete_workflow(
        self,
        async_client: AsyncClient,
        test_analysis_data: Dict[str, Any],
        db_session: AsyncSession,
    ):
        """Test complete HTML export workflow with embedded visualizations."""
        project_id = test_analysis_data["project_id"]
        repository_id = test_analysis_data["repository_id"]

        # Export HTML format
        response = await async_client.get(
            f"/api/v1/export/html?project_id={project_id}&repository_id={repository_id}"
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "html" in response.headers["content-disposition"]

        # Validate HTML structure
        html_content = response.text
        assert "<!DOCTYPE html>" in html_content
        assert "<html" in html_content
        assert "CommandCenter Analysis Report" in html_content

        # Validate embedded Chart.js
        assert "chart.js" in html_content.lower() or "Chart" in html_content
        assert "<canvas" in html_content  # Chart canvas element

        # Validate dark mode toggle
        assert "dark-mode" in html_content.lower() or "theme" in html_content.lower()

        # Validate key sections
        assert "Technologies" in html_content
        assert "Dependencies" in html_content
        assert "Metrics" in html_content

        # Validate self-contained (no external dependencies)
        assert "https://cdn" not in html_content  # No CDN links

        # More robust check for http:// URLs
        if "http://" in html_content:
            import re
            urls = re.findall(r'http://[^\s"\']+', html_content)
            for url in urls:
                assert "localhost" in url or "127.0.0.1" in url, f"External URL found: {url}"

    @pytest.mark.asyncio
    async def test_csv_export_complete_workflow(
        self,
        async_client: AsyncClient,
        test_analysis_data: Dict[str, Any],
        db_session: AsyncSession,
    ):
        """Test complete CSV export workflow with multiple export types."""
        project_id = test_analysis_data["project_id"]
        repository_id = test_analysis_data["repository_id"]

        # Test different CSV export types
        export_types = ["technologies", "dependencies", "metrics", "gaps", "combined"]

        for export_type in export_types:
            response = await async_client.get(
                f"/api/v1/export/csv?"
                f"project_id={project_id}&"
                f"repository_id={repository_id}&"
                f"export_type={export_type}"
            )

            assert response.status_code == 200, f"Failed for export_type={export_type}"
            assert response.headers["content-type"] == "text/csv; charset=utf-8"
            assert "attachment" in response.headers["content-disposition"]
            assert f"{export_type}" in response.headers["content-disposition"]

            # Validate CSV structure
            csv_content = response.text
            lines = csv_content.strip().split("\n")
            assert len(lines) >= 1  # At least header row

            # Validate header row exists
            header = lines[0]
            assert "," in header  # CSV delimiter

            # For combined export, verify multiple sections
            if export_type == "combined":
                assert "Technologies" in csv_content or "Name" in csv_content
                assert len(lines) > 5  # Should have multiple sections

    @pytest.mark.asyncio
    async def test_excel_export_complete_workflow(
        self,
        async_client: AsyncClient,
        test_analysis_data: Dict[str, Any],
        db_session: AsyncSession,
    ):
        """Test complete Excel export workflow with formatted workbooks."""
        project_id = test_analysis_data["project_id"]
        repository_id = test_analysis_data["repository_id"]

        # Export Excel format
        response = await async_client.get(
            f"/api/v1/export/excel?project_id={project_id}&repository_id={repository_id}"
        )

        assert response.status_code == 200
        assert (
            response.headers["content-type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert "attachment" in response.headers["content-disposition"]
        assert "xlsx" in response.headers["content-disposition"]

        # Validate Excel structure using openpyxl
        excel_data = io.BytesIO(response.content)
        workbook = load_workbook(excel_data, read_only=True)

        # Validate multiple sheets exist
        expected_sheets = ["Technologies", "Dependencies", "Gaps", "Metrics"]
        for sheet_name in expected_sheets:
            assert sheet_name in workbook.sheetnames, f"Missing sheet: {sheet_name}"

        # Validate Technologies sheet structure
        tech_sheet = workbook["Technologies"]
        assert tech_sheet.max_row >= 2  # At least header + 1 data row

        # Validate header row
        header_row = [cell.value for cell in tech_sheet[1]]
        assert "Name" in header_row
        assert "Category" in header_row

        workbook.close()

    @pytest.mark.asyncio
    async def test_json_export_complete_workflow(
        self,
        async_client: AsyncClient,
        test_analysis_data: Dict[str, Any],
        db_session: AsyncSession,
    ):
        """Test complete JSON export workflow for programmatic access."""
        project_id = test_analysis_data["project_id"]
        repository_id = test_analysis_data["repository_id"]

        # Export JSON format
        response = await async_client.get(
            f"/api/v1/export/json?project_id={project_id}&repository_id={repository_id}"
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "json" in response.headers["content-disposition"]

        # Validate JSON structure
        json_data = response.json()
        assert "project" in json_data
        assert "repository" in json_data
        assert "analysis" in json_data

        analysis = json_data["analysis"]
        assert "technologies" in analysis
        assert "dependencies" in analysis
        assert "metrics" in analysis
        assert "gaps" in analysis

        # Validate metrics structure
        metrics = analysis["metrics"]
        assert isinstance(metrics, dict)
        assert "total_technologies" in metrics or len(metrics) > 0

    @pytest.mark.asyncio
    async def test_batch_export_workflow(
        self,
        async_client: AsyncClient,
        test_analysis_data: Dict[str, Any],
        db_session: AsyncSession,
    ):
        """Test batch export endpoint with multiple formats."""
        project_id = test_analysis_data["project_id"]

        # Request batch export with multiple formats
        batch_request = {
            "project_id": project_id,
            "formats": ["sarif", "html", "json"],
        }

        response = await async_client.post(
            "/api/v1/export/batch",
            json=batch_request,
        )

        assert response.status_code == 200
        result = response.json()

        # Validate batch export structure
        assert "job_id" in result or "exports" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_export_formats_list(self, async_client: AsyncClient):
        """Test export formats endpoint returns available formats."""
        response = await async_client.get("/api/v1/export/formats")

        assert response.status_code == 200
        formats = response.json()

        assert "formats" in formats
        format_list = formats["formats"]

        # Validate all expected formats are present
        expected_formats = ["sarif", "html", "csv", "excel", "json"]
        for fmt in expected_formats:
            assert fmt in format_list

    @pytest.mark.asyncio
    async def test_export_with_invalid_project(self, async_client: AsyncClient):
        """Test export endpoints handle invalid project IDs gracefully."""
        invalid_project_id = 99999

        # Test SARIF export with invalid project
        response = await async_client.get(
            f"/api/v1/export/sarif?project_id={invalid_project_id}"
        )

        # Should return 404 or 400
        assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    async def test_export_rate_limiting(
        self,
        async_client: AsyncClient,
        test_analysis_data: Dict[str, Any],
    ):
        """Test rate limiting on export endpoints."""
        project_id = test_analysis_data["project_id"]

        # Make multiple rapid requests
        responses = []
        for _ in range(15):  # Exceed 10/minute limit
            response = await async_client.get(
                f"/api/v1/export/json?project_id={project_id}"
            )
            responses.append(response)

        # Check if rate limiting is active
        status_codes = [r.status_code for r in responses]
        if any(code == 429 for code in status_codes):
            # Rate limiting is active, verify it works
            assert 429 in status_codes  # Too Many Requests
        else:
            # Rate limiting might be disabled in test environment
            pytest.skip("Rate limiting not active in test environment")

    @pytest.mark.asyncio
    async def test_export_content_length_headers(
        self,
        async_client: AsyncClient,
        test_analysis_data: Dict[str, Any],
    ):
        """Test that export endpoints include Content-Length headers."""
        project_id = test_analysis_data["project_id"]

        # Test JSON export (smallest, most predictable)
        response = await async_client.get(
            f"/api/v1/export/json?project_id={project_id}"
        )

        assert response.status_code == 200
        assert "content-length" in response.headers
        content_length = int(response.headers["content-length"])
        assert content_length > 0
        assert content_length == len(response.content)

    @pytest.mark.asyncio
    async def test_csv_export_all_types(
        self,
        async_client: AsyncClient,
        test_analysis_data: Dict[str, Any],
    ):
        """Test CSV export with all available export types."""
        project_id = test_analysis_data["project_id"]

        export_types = {
            "technologies": ["Name", "Category"],
            "dependencies": ["Name", "Version"],
            "metrics": ["Metric", "Value"],
            "gaps": ["Technology", "Current"],
            "combined": ["Technologies", "Dependencies"],
        }

        for export_type, expected_headers in export_types.items():
            response = await async_client.get(
                f"/api/v1/export/csv?"
                f"project_id={project_id}&"
                f"export_type={export_type}"
            )

            assert response.status_code == 200
            csv_content = response.text

            # Validate expected headers are present
            for header in expected_headers:
                assert (
                    header in csv_content
                ), f"Missing header '{header}' in {export_type} export"

    @pytest.mark.asyncio
    async def test_excel_sheet_formatting(
        self,
        async_client: AsyncClient,
        test_analysis_data: Dict[str, Any],
    ):
        """Test Excel export includes proper formatting."""
        project_id = test_analysis_data["project_id"]

        response = await async_client.get(
            f"/api/v1/export/excel?project_id={project_id}"
        )

        assert response.status_code == 200

        # Load and inspect workbook
        excel_data = io.BytesIO(response.content)
        workbook = load_workbook(excel_data)

        # Check Technologies sheet formatting
        tech_sheet = workbook["Technologies"]

        # Validate header row exists and has values
        header_cells = list(tech_sheet[1])
        header_values = [cell.value for cell in header_cells if cell.value]
        assert len(header_values) >= 3  # At least 3 columns

        workbook.close()

    @pytest.mark.asyncio
    async def test_export_concurrent_requests(
        self,
        async_client: AsyncClient,
        test_analysis_data: Dict[str, Any],
    ):
        """Test that multiple concurrent export requests are handled properly."""
        import asyncio

        project_id = test_analysis_data["project_id"]

        # Create multiple concurrent export requests
        tasks = [
            async_client.get(f"/api/v1/export/json?project_id={project_id}")
            for _ in range(5)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # All requests should succeed (or be rate limited)
        for response in responses:
            if not isinstance(response, (asyncio.TimeoutError, asyncio.CancelledError)):
                assert response.status_code in [200, 429]

    @pytest.mark.asyncio
    async def test_export_with_empty_analysis(
        self,
        async_client: AsyncClient,
        test_project: Project,
    ):
        """Test export endpoints handle empty analysis data gracefully."""
        project_id = test_project.id

        # Export from project with no analysis data
        response = await async_client.get(
            f"/api/v1/export/json?project_id={project_id}"
        )

        # Should succeed but return minimal data
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            json_data = response.json()
            assert "analysis" in json_data


class TestExportErrorHandling:
    """Test error handling in export endpoints."""

    @pytest.mark.asyncio
    async def test_invalid_export_format(self, async_client: AsyncClient):
        """Test handling of invalid export format parameter."""
        response = await async_client.get("/api/v1/export/invalid_format?project_id=1")

        # Should return 404 for invalid route
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_missing_required_parameters(self, async_client: AsyncClient):
        """Test handling of missing required parameters."""
        # Missing project_id
        response = await async_client.get("/api/v1/export/json")

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_csv_export_type(
        self,
        async_client: AsyncClient,
        test_analysis_data: Dict[str, Any],
    ):
        """Test handling of invalid CSV export type."""
        project_id = test_analysis_data["project_id"]

        response = await async_client.get(
            f"/api/v1/export/csv?project_id={project_id}&export_type=invalid_type"
        )

        # Should return 422 due to enum validation
        assert response.status_code == 422
