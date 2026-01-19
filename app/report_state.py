"""
Report State Management

Central state tracking for the guided workflow.
Tracks report state through all pages and ensures
export only happens after final confirmation.
"""

from typing import Optional
from enum import Enum
from datetime import datetime
from copy import deepcopy

from app.report_model import ReportWorkspace


class ReportStatus(Enum):
    """Report status in the workflow."""
    UPLOADED = "uploaded"  # Page 1: Documents uploaded
    SCANNED = "scanned"  # Page 2: Scan completed
    DRAFT_GENERATED = "draft_generated"  # Page 3: Draft PDF generated
    IN_REVIEW = "in_review"  # Page 4: Review & edit mode
    FINAL_CONFIRMED = "final_confirmed"  # Page 5: User confirmed as final


class ReportState:
    """
    Central report state management.
    
    Tracks:
    - Uploaded document paths
    - Scan results
    - Report workspace
    - Draft PDF path
    - Final confirmation status
    - All edits and AI suggestions
    """
    
    def __init__(self) -> None:
        """Initialize empty report state."""
        self.status = ReportStatus.UPLOADED
        self.uploaded_paths: list[str] = []
        self.ingested_chunks: list[dict] = []
        self.enhanced_findings: list[dict] = []
        self.report_workspace: Optional[ReportWorkspace] = None
        self.report_data: Optional[dict] = None
        self.draft_pdf_path: Optional[str] = None
        self.is_final: bool = False
        self.final_confirmed_at: Optional[str] = None
    
    def set_uploaded(self, paths: list[str]) -> None:
        """Set uploaded document paths (Page 1)."""
        self.uploaded_paths = paths.copy()
        self.status = ReportStatus.UPLOADED
        self.is_final = False
        self.final_confirmed_at = None
    
    def set_scanned(self, chunks: list[dict], findings: list[dict]) -> None:
        """Set scan results (Page 2)."""
        self.ingested_chunks = deepcopy(chunks)
        self.enhanced_findings = deepcopy(findings)
        self.status = ReportStatus.SCANNED
    
    def set_draft_generated(self, pdf_path: str) -> None:
        """Set draft PDF path (Page 3)."""
        self.draft_pdf_path = pdf_path
        self.status = ReportStatus.DRAFT_GENERATED
    
    def set_in_review(self) -> None:
        """Enter review mode (Page 4)."""
        self.status = ReportStatus.IN_REVIEW
    
    def confirm_final(self) -> None:
        """Mark report as final (Page 5)."""
        self.is_final = True
        self.final_confirmed_at = datetime.utcnow().isoformat() + "Z"
        self.status = ReportStatus.FINAL_CONFIRMED
    
    def can_export(self) -> bool:
        """Check if report can be exported (only after final confirmation)."""
        return self.is_final and self.status == ReportStatus.FINAL_CONFIRMED
    
    def update_report_workspace(self, workspace: ReportWorkspace) -> None:
        """Update report workspace (after edits)."""
        self.report_workspace = workspace
    
    def update_report_data(self, data: dict) -> None:
        """Update report data (after edits)."""
        self.report_data = deepcopy(data)
    
    def reset(self) -> None:
        """Reset state for new workflow."""
        self.status = ReportStatus.UPLOADED
        self.uploaded_paths.clear()
        self.ingested_chunks.clear()
        self.enhanced_findings.clear()
        self.report_workspace = None
        self.report_data = None
        self.draft_pdf_path = None
        self.is_final = False
        self.final_confirmed_at = None
