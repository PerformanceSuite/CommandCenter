"""
Export API router for analysis results.

Provides endpoints to export analysis in multiple formats:
- SARIF (GitHub code scanning)
- HTML (interactive reports)
- CSV (spreadsheets)
- Excel (multi-sheet workbooks)
- JSON (raw data)
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Response
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.database import get_db
from app.models.project_analysis import ProjectAnalysis
from app.exporters.sarif import export_to_sarif
from app.exporters.html import export_to_html
from app.exporters.csv import export_to_csv, export_to_excel
from app.exporters import ExportFormat, UnsupportedFormatError, ExportDataError

router = APIRouter(prefix="/api/v1/export", tags=["Export"])


@router.get("/{analysis_id}/sarif")
async def export_analysis_sarif(
    analysis_id: int,
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Export analysis to SARIF 2.1.0 format.

    SARIF (Static Analysis Results Interchange Format) is consumed by:
    - GitHub Code Scanning
    - GitLab SAST
    - Azure DevOps
    - VS Code and other IDEs

    Args:
        analysis_id: Project analysis ID
        db: Database session

    Returns:
        SARIF JSON document

    Raises:
        HTTPException: 404 if analysis not found
    """
    analysis = db.query(ProjectAnalysis).filter(ProjectAnalysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    try:
        # Convert analysis to dict
        analysis_data = {
            "project_path": analysis.project_path,
            "analyzed_at": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
            "analysis_version": analysis.analysis_version,
            "detected_technologies": analysis.detected_technologies or {},
            "dependencies": analysis.dependencies or {},
            "code_metrics": analysis.code_metrics or {},
            "research_gaps": analysis.research_gaps or {},
        }

        sarif_data = export_to_sarif(analysis_data)

        return JSONResponse(
            content=sarif_data,
            headers={
                "Content-Disposition": f'attachment; filename="analysis_{analysis_id}.sarif"'
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export SARIF: {str(e)}"
        )


@router.get("/{analysis_id}/html")
async def export_analysis_html(
    analysis_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Export analysis to self-contained HTML report.

    Generates an interactive HTML dashboard with:
    - Charts and visualizations (Chart.js)
    - Dark/light mode toggle
    - Print-friendly styles
    - No external dependencies

    Args:
        analysis_id: Project analysis ID
        db: Database session

    Returns:
        HTML document

    Raises:
        HTTPException: 404 if analysis not found
    """
    analysis = db.query(ProjectAnalysis).filter(ProjectAnalysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    try:
        analysis_data = {
            "project_path": analysis.project_path,
            "analyzed_at": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
            "analysis_version": analysis.analysis_version,
            "detected_technologies": analysis.detected_technologies or {},
            "dependencies": analysis.dependencies or {},
            "code_metrics": analysis.code_metrics or {},
            "research_gaps": analysis.research_gaps or {},
        }

        html_content = export_to_html(analysis_data)

        return HTMLResponse(
            content=html_content,
            headers={
                "Content-Disposition": f'inline; filename="analysis_{analysis_id}.html"'
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export HTML: {str(e)}"
        )


@router.get("/{analysis_id}/csv")
async def export_analysis_csv(
    analysis_id: int,
    export_type: str = Query("combined", description="CSV type: technologies, dependencies, metrics, gaps, combined"),
    db: Session = Depends(get_db),
) -> Response:
    """
    Export analysis to CSV format.

    Generates CSV data that can be imported into Excel, Google Sheets, etc.

    Args:
        analysis_id: Project analysis ID
        export_type: Type of CSV to generate
        db: Database session

    Returns:
        CSV data

    Raises:
        HTTPException: 404 if analysis not found, 400 for invalid export type
    """
    valid_types = ["technologies", "dependencies", "metrics", "gaps", "combined"]
    if export_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid export_type. Must be one of: {', '.join(valid_types)}",
        )

    analysis = db.query(ProjectAnalysis).filter(ProjectAnalysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    try:
        analysis_data = {
            "project_path": analysis.project_path,
            "analyzed_at": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
            "analysis_version": analysis.analysis_version,
            "detected_technologies": analysis.detected_technologies or {},
            "dependencies": analysis.dependencies or {},
            "code_metrics": analysis.code_metrics or {},
            "research_gaps": analysis.research_gaps or {},
        }

        csv_content = export_to_csv(analysis_data, export_type)

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="analysis_{analysis_id}_{export_type}.csv"'
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export CSV: {str(e)}"
        )


@router.get("/{analysis_id}/excel")
async def export_analysis_excel(
    analysis_id: int,
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

    Args:
        analysis_id: Project analysis ID
        db: Database session

    Returns:
        Excel workbook

    Raises:
        HTTPException: 404 if analysis not found, 500 if openpyxl not installed
    """
    analysis = db.query(ProjectAnalysis).filter(ProjectAnalysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    try:
        analysis_data = {
            "project_path": analysis.project_path,
            "analyzed_at": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
            "analysis_version": analysis.analysis_version,
            "detected_technologies": analysis.detected_technologies or {},
            "dependencies": analysis.dependencies or {},
            "code_metrics": analysis.code_metrics or {},
            "research_gaps": analysis.research_gaps or {},
        }

        excel_bytes = export_to_excel(analysis_data)

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="analysis_{analysis_id}.xlsx"'
            },
        )

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Excel export requires openpyxl library. Install with: pip install openpyxl",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export Excel: {str(e)}"
        )


@router.get("/{analysis_id}/json")
async def export_analysis_json(
    analysis_id: int,
    pretty: bool = Query(True, description="Pretty-print JSON"),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Export analysis to JSON format.

    Returns raw analysis data as JSON.

    Args:
        analysis_id: Project analysis ID
        pretty: Whether to pretty-print JSON
        db: Database session

    Returns:
        JSON document

    Raises:
        HTTPException: 404 if analysis not found
    """
    analysis = db.query(ProjectAnalysis).filter(ProjectAnalysis.id == analysis_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    try:
        analysis_data = {
            "id": analysis.id,
            "project_path": analysis.project_path,
            "analyzed_at": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
            "analysis_version": analysis.analysis_version,
            "analysis_duration_ms": analysis.analysis_duration_ms,
            "detected_technologies": analysis.detected_technologies or {},
            "dependencies": analysis.dependencies or {},
            "code_metrics": analysis.code_metrics or {},
            "research_gaps": analysis.research_gaps or {},
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None,
        }

        return JSONResponse(
            content=analysis_data,
            headers={
                "Content-Disposition": f'attachment; filename="analysis_{analysis_id}.json"'
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export JSON: {str(e)}"
        )


@router.get("/formats")
async def get_available_formats() -> dict:
    """
    Get list of available export formats.

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
                "use_cases": ["GitHub Code Scanning", "GitLab SAST", "Azure DevOps", "IDE integration"],
            },
            {
                "name": "HTML",
                "format": "html",
                "endpoint": "/export/{analysis_id}/html",
                "mime_type": "text/html",
                "description": "Self-contained interactive HTML report with charts",
                "use_cases": ["Sharing reports", "Presentations", "Archiving", "Offline viewing"],
            },
            {
                "name": "CSV",
                "format": "csv",
                "endpoint": "/export/{analysis_id}/csv?export_type={type}",
                "mime_type": "text/csv",
                "description": "Spreadsheet-friendly CSV data",
                "use_cases": ["Excel/Google Sheets", "Data analysis", "Custom processing"],
                "parameters": {
                    "export_type": ["technologies", "dependencies", "metrics", "gaps", "combined"]
                },
            },
            {
                "name": "Excel",
                "format": "excel",
                "endpoint": "/export/{analysis_id}/excel",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "description": "Multi-sheet Excel workbook with formatting",
                "use_cases": ["Professional reports", "Executive summaries", "Data analysis"],
                "requires": "openpyxl library",
            },
            {
                "name": "JSON",
                "format": "json",
                "endpoint": "/export/{analysis_id}/json",
                "mime_type": "application/json",
                "description": "Raw analysis data in JSON format",
                "use_cases": ["API integration", "Custom processing", "Data backup"],
            },
        ]
    }


@router.post("/batch")
async def export_batch_analyses(
    analysis_ids: list[int],
    format: str = Query("json", description="Export format: sarif, html, csv, excel, json"),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Export multiple analyses in batch.

    Returns a job ID for tracking the batch export operation.
    Use the jobs API to monitor progress and download results.

    Args:
        analysis_ids: List of analysis IDs to export
        format: Export format
        db: Database session

    Returns:
        Job information

    Raises:
        HTTPException: 400 for invalid format or empty list
    """
    valid_formats = ["sarif", "html", "csv", "excel", "json"]
    if format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}",
        )

    if not analysis_ids:
        raise HTTPException(
            status_code=400,
            detail="analysis_ids cannot be empty",
        )

    # Verify all analyses exist
    analyses = db.query(ProjectAnalysis).filter(ProjectAnalysis.id.in_(analysis_ids)).all()
    found_ids = {a.id for a in analyses}
    missing_ids = set(analysis_ids) - found_ids

    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Analyses not found: {', '.join(map(str, missing_ids))}",
        )

    # TODO: Create batch export job using job service
    # For now, return placeholder

    return JSONResponse(
        content={
            "message": "Batch export job created",
            "job_id": None,  # TODO: Replace with actual job ID
            "analysis_count": len(analysis_ids),
            "format": format,
            "status": "pending",
            "note": "Batch export implementation pending - use individual export endpoints for now",
        },
        status_code=202,  # Accepted
    )
