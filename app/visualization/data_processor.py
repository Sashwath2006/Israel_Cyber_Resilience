"""
Data Processing and Analytics for Vulnerability Findings

Aggregates finding data into analyzable formats for chart generation.
Calculates risk metrics and statistical distributions.
"""

from typing import Dict, List, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass


@dataclass
class ChartData:
    """Container for processed chart data."""
    severity_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    file_distribution: Dict[str, int]
    confidence_distribution: Dict[str, int]
    risk_score: float
    total_findings: int
    high_count: int
    medium_count: int
    low_count: int


class ReportAnalytics:
    """
    Analyzes vulnerability findings and computes statistics for visualization.
    
    Responsibilities:
    - Aggregate findings by severity, category, file, confidence
    - Calculate risk score
    - Prepare data for chart generation
    - Handle edge cases (empty findings, invalid data)
    """
    
    # Severity levels for ordering
    SEVERITY_ORDER = ["High", "Medium", "Low"]
    SEVERITY_WEIGHTS = {"High": 3, "Medium": 2, "Low": 1}
    
    # Confidence score ranges for histogram
    CONFIDENCE_RANGES = [
        (0.0, 0.2),
        (0.2, 0.4),
        (0.4, 0.6),
        (0.6, 0.8),
        (0.8, 1.0),
    ]
    
    def __init__(self, findings: List[dict]):
        """
        Initialize with findings list.
        
        Args:
            findings: List of finding dictionaries from rule engine
        """
        self.findings = findings
        self.active_findings = [f for f in findings if not f.get("suppressed", False)]
    
    def get_severity_distribution(self) -> Dict[str, int]:
        """Get count of findings by severity level."""
        if not self.active_findings:
            return {"High": 0, "Medium": 0, "Low": 0}
        
        dist = Counter()
        for finding in self.active_findings:
            severity = finding.get("severity", "Low")
            dist[severity] += 1
        
        # Ensure all severity levels are present
        for level in self.SEVERITY_ORDER:
            if level not in dist:
                dist[level] = 0
        
        return dict(dist)
    
    def get_category_distribution(self) -> Dict[str, int]:
        """Get count of findings by category."""
        if not self.active_findings:
            return {}
        
        dist = Counter()
        for finding in self.active_findings:
            category = finding.get("category", "Unknown")
            dist[category] += 1
        
        # Sort by count (descending)
        return dict(sorted(dist.items(), key=lambda x: x[1], reverse=True))
    
    def get_file_distribution(self) -> Dict[str, int]:
        """Get count of findings per file."""
        if not self.active_findings:
            return {}
        
        dist = Counter()
        for finding in self.active_findings:
            locations = finding.get("locations", [])
            if locations:
                for loc in locations:
                    file_path = loc.get("file", "Unknown")
                    # Simplify path to filename
                    filename = file_path.split("\\")[-1] if "\\" in file_path else file_path
                    dist[filename] += 1
            else:
                dist["Unknown"] += 1
        
        # Sort by count (descending), limit to top 10 for readability
        sorted_list = sorted(dist.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_list) > 10:
            top_10 = dict(sorted_list[:10])
            others_count = sum(v for k, v in sorted_list[10:])
            if others_count > 0:
                top_10["Others"] = others_count
            return top_10
        
        return dict(sorted_list)
    
    def get_confidence_distribution(self) -> Dict[str, int]:
        """Get histogram of findings by confidence score ranges."""
        if not self.active_findings:
            return {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
        
        dist = {}
        for low, high in self.CONFIDENCE_RANGES:
            key = f"{low:.1f}-{high:.1f}"
            dist[key] = 0
        
        for finding in self.active_findings:
            confidence = float(finding.get("confidence", 0.0))
            for low, high in self.CONFIDENCE_RANGES:
                if low <= confidence < high or (high == 1.0 and confidence == 1.0):
                    key = f"{low:.1f}-{high:.1f}"
                    dist[key] += 1
                    break
        
        return dist
    
    def calculate_risk_score(self) -> float:
        """
        Calculate overall risk score (0-100) based on findings.
        
        Formula: (high*3 + medium*2 + low*1) / max_possible * 100
        
        Returns:
            Risk score from 0-100
        """
        if not self.active_findings:
            return 0.0
        
        severity_dist = self.get_severity_distribution()
        high_count = severity_dist.get("High", 0)
        medium_count = severity_dist.get("Medium", 0)
        low_count = severity_dist.get("Low", 0)
        
        # Calculate weighted score
        weighted_score = (high_count * 3) + (medium_count * 2) + (low_count * 1)
        
        # Calculate maximum possible score
        total_findings = len(self.active_findings)
        max_score = total_findings * 3  # If all were High
        
        if max_score == 0:
            return 0.0
        
        # Normalize to 0-100
        risk_score = min(100.0, (weighted_score / max_score) * 100)
        return round(risk_score, 1)
    
    def get_chart_data(self) -> ChartData:
        """
        Get all processed data needed for chart generation.
        
        Returns:
            ChartData object with all aggregated analytics
        """
        severity_dist = self.get_severity_distribution()
        
        return ChartData(
            severity_distribution=severity_dist,
            category_distribution=self.get_category_distribution(),
            file_distribution=self.get_file_distribution(),
            confidence_distribution=self.get_confidence_distribution(),
            risk_score=self.calculate_risk_score(),
            total_findings=len(self.active_findings),
            high_count=severity_dist.get("High", 0),
            medium_count=severity_dist.get("Medium", 0),
            low_count=severity_dist.get("Low", 0),
        )
    
    @staticmethod
    def get_risk_level(risk_score: float) -> str:
        """
        Get risk level label based on score.
        
        Args:
            risk_score: Score from 0-100
            
        Returns:
            Risk level: "Critical", "High", "Medium", "Low", or "Minimal"
        """
        if risk_score >= 80:
            return "Critical"
        elif risk_score >= 60:
            return "High"
        elif risk_score >= 40:
            return "Medium"
        elif risk_score >= 20:
            return "Low"
        else:
            return "Minimal"
