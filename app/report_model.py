"""
Report Workspace Model (Phase 10)

A living, editable report model that aggregates findings, stores executive
summary, and allows analyst edits. The report reflects severity overrides
immediately and can be refined via user edits and chat.

The report is stored in memory and serializable on user request.
No auto-save without consent.
"""

from typing import Optional
from datetime import datetime
from copy import deepcopy


class ReportWorkspace:
    """
    Editable report workspace that aggregates findings and executive summary.
    
    This model:
    - Stores executive summary as editable text
    - Aggregates findings with their evidence, confidence, and final severity
    - Allows analyst notes per finding
    - Supports serialization for export/save
    - Does not auto-save (explicit user action required)
    - Reflects severity overrides immediately
    """
    
    def __init__(
        self,
        scope: Optional[str] = None,
        analyst_name: Optional[str] = None,
        executive_summary: str = "",
    ) -> None:
        """
        Initialize a new report workspace.
        
        Args:
            scope: Optional scope description (e.g., "Production Config Files")
            analyst_name: Optional analyst name
            executive_summary: Initial executive summary text (default: empty)
        """
        self.scope = scope
        self.analyst_name = analyst_name
        self.executive_summary = executive_summary
        self.created_at = datetime.utcnow().isoformat() + "Z"
        self.updated_at = self.created_at
        
        # Findings are stored with full metadata
        # Each finding includes: evidence, confidence, final_severity, analyst_notes
        self.findings: list[dict] = []
    
    def add_findings(self, findings: list[dict]) -> None:
        """
        Add findings to the report.
        
        Findings are copied to avoid external modifications affecting the report.
        Each finding must have severity override fields initialized.
        
        Args:
            findings: List of finding dictionaries with severity fields
        
        Note:
            Duplicate findings (same finding_id) are not automatically deduplicated.
            Caller should manage this if needed.
        """
        # Deep copy to avoid external modifications
        copied_findings = deepcopy(findings)
        
        # Ensure each finding has required fields for report
        for finding in copied_findings:
            # Initialize analyst_notes if not present
            if "analyst_notes" not in finding:
                finding["analyst_notes"] = None
        
        self.findings.extend(copied_findings)
        self.updated_at = datetime.utcnow().isoformat() + "Z"
    
    def update_executive_summary(self, summary: str) -> None:
        """
        Update the executive summary text.
        
        Args:
            summary: New executive summary text
        """
        self.executive_summary = summary
        self.updated_at = datetime.utcnow().isoformat() + "Z"
    
    def update_finding(
        self,
        finding_id: str,
        updates: dict,
    ) -> bool:
        """
        Update a specific finding in the report.
        
        This allows updating analyst_notes, final_severity (via override),
        or other editable fields. Evidence is immutable.
        
        Args:
            finding_id: ID of the finding to update
            updates: Dictionary of fields to update (e.g., {"analyst_notes": "..."})
        
        Returns:
            True if finding was found and updated, False otherwise
        
        Note:
            This updates the finding in-place. For severity overrides, use
            severity_override.override_severity() first, then update_finding().
        """
        for finding in self.findings:
            if finding.get("finding_id") == finding_id:
                # Update allowed fields
                # Evidence is immutable - do not allow updates to evidence
                for key, value in updates.items():
                    if key == "evidence":
                        # Evidence is immutable - skip
                        continue
                    finding[key] = value
                
                self.updated_at = datetime.utcnow().isoformat() + "Z"
                return True
        
        return False
    
    def add_analyst_notes(self, finding_id: str, notes: str) -> bool:
        """
        Add analyst notes to a specific finding.
        
        Args:
            finding_id: ID of the finding
            notes: Analyst notes text
        
        Returns:
            True if finding was found and notes added, False otherwise
        """
        return self.update_finding(finding_id, {"analyst_notes": notes})
    
    def get_findings_by_severity(
        self,
        severity: Optional[str] = None,
        include_suppressed: bool = False,
    ) -> list[dict]:
        """
        Get findings filtered by severity.
        
        Args:
            severity: Severity to filter by ("High", "Medium", "Low"), or None for all
            include_suppressed: If True, include suppressed findings
        
        Returns:
            List of findings matching the filter
        """
        from app.severity_override import get_final_severity
        
        filtered = []
        
        for finding in self.findings:
            # Filter by suppression
            if not include_suppressed and finding.get("suppressed", False):
                continue
            
            # Filter by severity if specified
            if severity:
                final_sev = get_final_severity(finding)
                if final_sev != severity:
                    continue
            
            filtered.append(deepcopy(finding))
        
        return filtered
    
    def to_dict(self) -> dict:
        """
        Serialize the report to a dictionary.
        
        This allows saving the report to JSON or other formats.
        
        Returns:
            Dictionary representation of the report
        """
        return {
            "scope": self.scope,
            "analyst_name": self.analyst_name,
            "executive_summary": self.executive_summary,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "findings": deepcopy(self.findings),
            "metadata": {
                "total_findings": len(self.findings),
                "findings_by_severity": self._count_by_severity(),
            },
        }
    
    def _count_by_severity(self) -> dict[str, int]:
        """Count findings by final severity."""
        from app.severity_override import get_final_severity
        
        counts = {"High": 0, "Medium": 0, "Low": 0}
        
        for finding in self.findings:
            if not finding.get("suppressed", False):
                final_sev = get_final_severity(finding)
                counts[final_sev] = counts.get(final_sev, 0) + 1
        
        return counts
    
    @classmethod
    def from_dict(cls, data: dict) -> "ReportWorkspace":
        """
        Deserialize a report from a dictionary.
        
        Args:
            data: Dictionary representation of the report
        
        Returns:
            ReportWorkspace instance
        """
        report = cls(
            scope=data.get("scope"),
            analyst_name=data.get("analyst_name"),
            executive_summary=data.get("executive_summary", ""),
        )
        
        # Restore timestamps if present
        if "created_at" in data:
            report.created_at = data["created_at"]
        if "updated_at" in data:
            report.updated_at = data["updated_at"]
        
        # Restore findings
        if "findings" in data:
            report.findings = deepcopy(data["findings"])
        
        return report
    
    def get_summary_stats(self) -> dict:
        """
        Get summary statistics for the report.
        
        Returns:
            Dictionary with counts and statistics
        """
        from app.severity_override import get_final_severity
        
        total = len(self.findings)
        suppressed = sum(1 for f in self.findings if f.get("suppressed", False))
        active = total - suppressed
        
        severity_counts = self._count_by_severity()
        
        return {
            "total_findings": total,
            "active_findings": active,
            "suppressed_findings": suppressed,
            "severity_breakdown": severity_counts,
            "overridden_severities": sum(
                1 for f in self.findings if f.get("severity_overridden", False)
            ),
        }
