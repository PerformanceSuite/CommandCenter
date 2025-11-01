"""
Export API router for analysis results.

Provides endpoints to export analysis in multiple formats:
- SARIF (GitHub code scanning)
- HTML (interactive reports)
- CSV (spreadsheets)
- Excel (multi-sheet workbooks)
- JSON (raw data)
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Response, Request
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from enum import Enum
import json
import logging

from app.database import get_db
from app.models.project_analysis import ProjectAnalysis
from app.exporters.sarif import export_to_sarif
from app.exporters.html import export_to_html
from app.exporters.csv import export_to_csv, export_to_excel
from app.exporters import ExportFormat, UnsupportedFormatError, ExportDataError
from app.middleware import limiter

router = APIRouter(prefix="/api/v1/export", tags=["Export"])
logger = logging.getLogger(__name__)


class CSVExportType(str, Enum):
    """Valid CSV export types."""

    COMBINED = "combined"
    TECHNOLOGIES = "technologies"
    DEPENDENCIES = "dependencies"
    METRICS = "metrics"
    GAPS = "gaps"


class ExportFormatEnum(str, Enum):
    """Valid export formats for batch operations."""

    SARIF = "sarif"
    HTML = "html"
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"


def _get_analysis_data(analysis: ProjectAnalysis) -> dict:
    """
    Convert ProjectAnalysis model to dictionary for exporters.

    Args:
        analysis: ProjectAnalysis model instance

    Returns:
        Dictionary with analysis data
    """
    return {
        "id": analysis.id,
        "project_path": analysis.project_path,
        "analyzed_at": (
            analysis.analyzed_at.isoformat() if analysis.analyzed_at else None
        ),
        "analysis_version": analysis.analysis_version,
        "analysis_duration_ms": analysis.analysis_duration_ms,
        "detected_technologies": analysis.detected_technologies or {},
        "dependencies": analysis.dependencies or {},
        "code_metrics": analysis.code_metrics or {},
        "research_gaps": analysis.research_gaps or {},
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None,
    }


@router.get("/{analysis_id}/sarif")
@limiter.limit("10/minute")
async def export_analysis_sarif(
    analysis_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Export analysis to SARIF 2.1.0 format.

    SARIF (Static Analysis Results Interchange Format) is consumed by:
    - GitHub Code Scanning
    - GitLab SAST
    - Azure DevOps
    - VS Code and other IDEs

    Rate limit: 10 requests per minute per user.

    Args:
        analysis_id: Project analysis ID
        db: Database session

    Returns:
        SARIF JSON document

    Raises:
        HTTPException: 404 if analysis not found, 500 on export failure
    """
    logger.info(f"SARIF export requested for analysis {analysis_id}")

    analysis = (
        db.query(ProjectAnalysis).filter(ProjectAnalysis.id == analysis_id).first()
    )

    if not analysis:
        logger.warning(f"Analysis {analysis_id} not found for SARIF export")
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    try:
        analysis_data = _get_analysis_data(analysis)
        sarif_data = export_to_sarif(analysis_data)

        sarif_json = json.dumps(sarif_data, indent=2)
        content_length = len(sarif_json.encode("utf-8"))

        logger.info(
            f"SARIF export successful for analysis {analysis_id}, size: {content_length} bytes"
        )

        return JSONResponse(
            content=sarif_data,
            headers={
                "Content-Disposition": f'attachment; filename="analysis_{analysis_id}.sarif"',
                "Content-Length": str(content_length),
            },
        )

    except Exception as e:
        logger.error(
            f"SARIF export failed for analysis {analysis_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to export SARIF: {str(e)}")


@router.get("/{analysis_id}/html")
@limiter.limit("10/minute")
async def export_analysis_html(
    analysis_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Export analysis to self-contained HTML report.

    Generates an interactive HTML dashboard with:
    - Charts and visualizations (Chart.js CDN)
    - Dark/light mode toggle
    - Responsive design
    - Print-friendly styles

    Rate limit: 10 requests per minute per user.

    Args:
        analysis_id: Project analysis ID
        db: Database session

    Returns:
        HTML document

    Raises:
        HTTPException: 404 if analysis not found, 500 on export failure
    """
    logger.info(f"HTML export requested for analysis {analysis_id}")

    analysis = (
        db.query(ProjectAnalysis).filter(ProjectAnalysis.id == analysis_id).first()
    )

    if not analysis:
        logger.warning(f"Analysis {analysis_id} not found for HTML export")
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    try:
        analysis_data = _get_analysis_data(analysis)
        html_content = export_to_html(analysis_data)
        content_length = len(html_content.encode("utf-8"))

        logger.info(
            f"HTML export successful for analysis {analysis_id}, size: {content_length} bytes"
        )

        return HTMLResponse(
            content=html_content,
            headers={
                "Content-Disposition": f'inline; filename="analysis_{analysis_id}.html"',
                "Content-Length": str(content_length),
            },
        )

    except Exception as e:
        logger.error(
            f"HTML export failed for analysis {analysis_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to export HTML: {str(e)}")


@router.get("/{analysis_id}/csv")
@limiter.limit("10/minute")
async def export_analysis_csv(
    analysis_id: int,
    request: Request,
    export_type: CSVExportType = Query(
        CSVExportType.COMBINED, description="CSV type to generate"
    ),
    db: Session = Depends(get_db),
) -> Response:
    """
    Export analysis to CSV format.

    Generates CSV data that can be imported into Excel, Google Sheets, etc.

    Rate limit: 10 requests per minute per user.

    Args:
        analysis_id: Project analysis ID
        export_type: Type of CSV to generate (validated enum)
        db: Database session

    Returns:
        CSV data

    Raises:
        HTTPException: 404 if analysis not found, 500 on export failure
    """
    logger.info(
        f"CSV export ({export_type.value}) requested for analysis {analysis_id}"
    )

    analysis = (
        db.query(ProjectAnalysis).filter(ProjectAnalysis.id == analysis_id).first()
    )

    if not analysis:
        logger.warning(f"Analysis {analysis_id} not found for CSV export")
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    try:
        analysis_data = _get_analysis_data(analysis)
        csv_content = export_to_csv(analysis_data, export_type.value)
        content_length = len(csv_content.encode("utf-8"))

        logger.info(
            f"CSV export ({export_type.value}) successful for analysis {analysis_id}, size: {content_length} bytes"
        )

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="analysis_{analysis_id}_{export_type.value}.csv"',
                "Content-Length": str(content_length),
            },
        )

    except Exception as e:
        logger.error(
            f"CSV export failed for analysis {analysis_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")


@router.get("/{analysis_id}/excel")
@limiter.limit("10/minute")
async def export_analysis_excel(
    analysis_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    """
    Export analysis to Excel (.xlsx) format.

    Generates multi-sheet workbook with formatting:
    - Summary sheet
    - Technologies sheet
    - Dependencies sheet
    - Metrics sheet
    - Research gaps sheet

    Requires openpyxl library.

    Rate limit: 10 requests per minute per user.

    Args:
        analysis_id: Project analysis ID
        db: Database session

    Returns:
        Excel workbook

    Raises:
        HTTPException: 404 if analysis not found, 500 if openpyxl not installed or export fails
    """
    logger.info(f"Excel export requested for analysis {analysis_id}")

    analysis = (
        db.query(ProjectAnalysis).filter(ProjectAnalysis.id == analysis_id).first()
    )

    if not analysis:
        logger.warning(f"Analysis {analysis_id} not found for Excel export")
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    try:
        analysis_data = _get_analysis_data(analysis)
        excel_bytes = export_to_excel(analysis_data)
        content_length = len(excel_bytes)

        logger.info(
            f"Excel export successful for analysis {analysis_id}, size: {content_length} bytes"
        )

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="analysis_{analysis_id}.xlsx"',
                "Content-Length": str(content_length),
            },
        )

    except ImportError as e:
        logger.error(f"Excel export failed - openpyxl not installed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Excel export requires openpyxl library. Install with: pip install openpyxl",
        )
    except Exception as e:
        logger.error(
            f"Excel export failed for analysis {analysis_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to export Excel: {str(e)}")


@router.get("/{analysis_id}/json")
@limiter.limit("10/minute")
async def export_analysis_json(
    analysis_id: int,
    request: Request,
    pretty: bool = Query(True, description="Pretty-print JSON"),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Export analysis to JSON format.

    Returns raw analysis data as JSON.

    Rate limit: 10 requests per minute per user.

    Args:
        analysis_id: Project analysis ID
        pretty: Whether to pretty-print JSON
        db: Database session

    Returns:
        JSON document

    Raises:
        HTTPException: 404 if analysis not found, 500 on export failure
    """
    logger.info(f"JSON export requested for analysis {analysis_id}")

    analysis = (
        db.query(ProjectAnalysis).filter(ProjectAnalysis.id == analysis_id).first()
    )

    if not analysis:
        logger.warning(f"Analysis {analysis_id} not found for JSON export")
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    try:
        analysis_data = _get_analysis_data(analysis)

        # Calculate content length
        json_str = json.dumps(analysis_data, indent=2 if pretty else None)
        content_length = len(json_str.encode("utf-8"))

        logger.info(
            f"JSON export successful for analysis {analysis_id}, size: {content_length} bytes"
        )

        return JSONResponse(
            content=analysis_data,
            headers={
                "Content-Disposition": f'attachment; filename="analysis_{analysis_id}.json"',
                "Content-Length": str(content_length),
            },
        )

    except Exception as e:
        logger.error(
            f"JSON export failed for analysis {analysis_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to export JSON: {str(e)}")


@router.get("/formats")
async def get_available_formats() -> dict:
    """
    Get list of available export formats.

    No rate limit on this informational endpoint.

    Returns:
        Dictionary of available formats with descriptions
    """
    return {
        "formats": [
            {
                "name": "SARIF",
                "format": "sarif",
                "endpoint": "/export/{analysis_id}/sarif",
                "mime_type": "application/json",
                "description": "Static Analysis Results Interchange Format (GitHub code scanning compatible)",
                "use_cases": [
                    "GitHub Code Scanning",
                    "GitLab SAST",
                    "Azure DevOps",
                    "IDE integration",
                ],
                "rate_limit": "10/minute",
            },
            {
                "name": "HTML",
                "format": "html",
                "endpoint": "/export/{analysis_id}/html",
                "mime_type": "text/html",
                "description": "Self-contained interactive HTML report with charts",
                "use_cases": [
                    "Sharing reports",
                    "Presentations",
                    "Archiving",
                    "Offline viewing",
                ],
                "rate_limit": "10/minute",
            },
            {
                "name": "CSV",
                "format": "csv",
                "endpoint": "/export/{analysis_id}/csv?export_type={type}",
                "mime_type": "text/csv",
                "description": "Spreadsheet-friendly CSV data",
                "use_cases": [
                    "Excel/Google Sheets",
                    "Data analysis",
                    "Custom processing",
                ],
                "parameters": {
                    "export_type": [
                        "technologies",
                        "dependencies",
                        "metrics",
                        "gaps",
                        "combined",
                    ]
                },
                "rate_limit": "10/minute",
            },
            {
                "name": "Excel",
                "format": "excel",
                "endpoint": "/export/{analysis_id}/excel",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "description": "Multi-sheet Excel workbook with formatting",
                "use_cases": [
                    "Professional reports",
                    "Executive summaries",
                    "Data analysis",
                ],
                "requires": "openpyxl library",
                "rate_limit": "10/minute",
            },
            {
                "name": "JSON",
                "format": "json",
                "endpoint": "/export/{analysis_id}/json",
                "mime_type": "application/json",
                "description": "Raw analysis data in JSON format",
                "use_cases": ["API integration", "Custom processing", "Data backup"],
                "rate_limit": "10/minute",
            },
        ]
    }


@router.post("/batch")
@limiter.limit("5/minute")
async def export_batch_analyses(
    request: Request,
    analysis_ids: list[int],
    format: ExportFormatEnum = Query(
        ExportFormatEnum.JSON, description="Export format"
    ),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Export multiple analyses in batch.

    Returns a job ID for tracking the batch export operation.
    Use the jobs API to monitor progress and download results.

    Rate limit: 5 requests per minute per user (lower due to resource intensity).

    Args:
        analysis_ids: List of analysis IDs to export
        format: Export format (validated enum)
        db: Database session

    Returns:
        Job information

    Raises:
        HTTPException: 400 for empty list, 404 if analyses not found
    """
    logger.info(
        f"Batch export requested for {len(analysis_ids)} analyses in {format.value} format"
    )

    if not analysis_ids:
        raise HTTPException(
            status_code=400,
            detail="analysis_ids cannot be empty",
        )

    # Verify all analyses exist
    analyses = (
        db.query(ProjectAnalysis).filter(ProjectAnalysis.id.in_(analysis_ids)).all()
    )
    found_ids = {a.id for a in analyses}
    missing_ids = set(analysis_ids) - found_ids

    if missing_ids:
        logger.warning(f"Batch export failed - analyses not found: {missing_ids}")
        raise HTTPException(
            status_code=404,
            detail=f"Analyses not found: {', '.join(map(str, missing_ids))}",
        )

    # TODO: Create batch export job using job service
    # For now, return placeholder
    logger.info(f"Batch export placeholder returned for {len(analysis_ids)} analyses")

    return JSONResponse(
        content={
            "message": "Batch export job created",
            "job_id": None,  # TODO: Replace with actual job ID from JobService
            "analysis_count": len(analysis_ids),
            "format": format.value,
            "status": "pending",
            "note": "Batch export implementation pending - use individual export endpoints for now",
        },
        status_code=202,  # Accepted
    )
