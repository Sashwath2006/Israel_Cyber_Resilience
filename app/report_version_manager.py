"""
Report Version Manager (Phase 14 - Part 2)

Provides snapshotting, version tracking, and undo/rollback functionality
for the report editing system.

Every edit is reversible:
- Save snapshot before applying changes
- Track all edit history
- Support rollback to any previous version
- Annotate snapshots with metadata
"""

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
from copy import deepcopy
from enum import Enum

from app.logging_config import get_logger

logger = get_logger("ReportVersionManager")


class ChangeType(Enum):
    """Type of change made to report."""
    INITIAL = "initial"
    MANUAL_EDIT = "manual_edit"
    AI_EDIT = "ai_edit"
    BULK_EDIT = "bulk_edit"
    IMPORT = "import"
    RESTORE = "restore"


@dataclass
class Snapshot:
    """A point-in-time snapshot of the report."""

    snapshot_id: str
    timestamp: str
    change_type: ChangeType
    section: Optional[str]  # Which section was edited (None for full report)
    old_content: Optional[str]  # For AI edits, store what changed
    new_content: Optional[str]  # For AI edits, store what changed
    description: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "change_type": self.change_type.value,
            "section": self.section,
            "old_content": self.old_content,
            "new_content": self.new_content,
            "description": self.description,
            "metadata": self.metadata,
        }


@dataclass
class ReportVersion:
    """A complete report version at a point in time."""

    version_id: str
    timestamp: str
    report_content: dict  # Full report structure
    snapshot: Snapshot
    is_current: bool = False

    def to_dict(self) -> dict:
        return {
            "version_id": self.version_id,
            "timestamp": self.timestamp,
            "report_content": self.report_content,
            "snapshot": self.snapshot.to_dict(),
            "is_current": self.is_current,
        }


class ReportVersionManager:
    """
    Manages report versions, snapshots, and undo/rollback.

    Features:
    - Snapshot before every edit
    - Full version history
    - Rollback to any version
    - Diff between versions
    - Metadata tracking
    """

    def __init__(self, max_versions: int = 50):
        """
        Initialize version manager.

        Args:
            max_versions: Maximum versions to keep (older ones auto-pruned)
        """
        self.max_versions = max_versions
        self.versions: list[ReportVersion] = []
        self.current_version_idx: int = -1
        self._snapshot_counter = 0

    def save_snapshot(
        self,
        report_content: dict,
        change_type: ChangeType,
        description: str,
        section: Optional[str] = None,
        old_content: Optional[str] = None,
        new_content: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> ReportVersion:
        """
        Save a snapshot of the current report state.

        Args:
            report_content: Full report structure to save
            change_type: Type of change (AI edit, manual, etc.)
            description: Human-readable description of the change
            section: Which section was edited (optional)
            old_content: For AI edits, the old text
            new_content: For AI edits, the new text
            metadata: Additional metadata to track

        Returns:
            ReportVersion object
        """
        self._snapshot_counter += 1
        snapshot_id = f"snap-{self._snapshot_counter:06d}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Create snapshot metadata
        snapshot = Snapshot(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            change_type=change_type,
            section=section,
            old_content=old_content,
            new_content=new_content,
            description=description,
            metadata=metadata or {},
        )

        # Create version
        version_id = f"v{len(self.versions) + 1:04d}"
        version = ReportVersion(
            version_id=version_id,
            timestamp=timestamp,
            report_content=deepcopy(report_content),
            snapshot=snapshot,
            is_current=True,
        )

        # Mark old current version as no longer current
        if self.current_version_idx >= 0 and self.current_version_idx < len(self.versions):
            self.versions[self.current_version_idx].is_current = False

        # Add to history
        self.versions.append(version)
        self.current_version_idx = len(self.versions) - 1

        # Prune old versions if needed
        if len(self.versions) > self.max_versions:
            self._prune_old_versions()
            # After pruning, update current_version_idx
            self.current_version_idx = len(self.versions) - 1

        logger.info(f"Saved snapshot {snapshot_id}: {description}")
        return version

    def get_current_version(self) -> Optional[ReportVersion]:
        """Get the current report version."""
        if self.current_version_idx >= 0:
            return self.versions[self.current_version_idx]
        return None

    def get_version(self, version_id: str) -> Optional[ReportVersion]:
        """
        Get a specific version by ID.

        Args:
            version_id: Version ID to retrieve

        Returns:
            ReportVersion or None if not found
        """
        for version in self.versions:
            if version.version_id == version_id:
                return version
        return None

    def list_versions(self) -> list[ReportVersion]:
        """
        List all versions in chronological order.

        Returns:
            List of ReportVersion objects
        """
        return list(self.versions)

    def rollback(self, version_id: str) -> tuple[bool, str]:
        """
        Rollback to a previous version.

        Args:
            version_id: Version ID to rollback to

        Returns:
            (success, message)
        """
        version = self.get_version(version_id)
        if not version:
            return False, f"Version {version_id} not found"

        # Mark old current as not current
        if self.current_version_idx >= 0:
            self.versions[self.current_version_idx].is_current = False

        # Find index and set as current
        for i, v in enumerate(self.versions):
            if v.version_id == version_id:
                self.current_version_idx = i
                v.is_current = True

                # Save a restore snapshot
                restore_snapshot = Snapshot(
                    snapshot_id=f"snap-{self._snapshot_counter + 1:06d}",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    change_type=ChangeType.RESTORE,
                    section=None,
                    old_content=None,
                    new_content=None,
                    description=f"Restored to {version_id}",
                    metadata={"restored_from": version_id},
                )
                self._snapshot_counter += 1

                logger.info(f"Rolled back to {version_id}")
                return True, f"Rolled back to {version_id}"

        return False, f"Failed to rollback to {version_id}"

    def undo_last(self) -> tuple[bool, str, Optional[ReportVersion]]:
        """
        Undo the last change (rollback to previous version).

        Returns:
            (success, message, previous_version)
        """
        if len(self.versions) < 2:
            return False, "Nothing to undo", None

        # Get the version before current
        previous_version = self.versions[len(self.versions) - 2]
        success, msg = self.rollback(previous_version.version_id)

        if success:
            return True, f"Undone: {previous_version.snapshot.description}", previous_version
        return False, msg, None

    def get_version_history(self) -> list[dict]:
        """
        Get a summary of all versions.

        Returns:
            List of version summaries
        """
        history = []
        for v in self.versions:
            history.append({
                "version_id": v.version_id,
                "timestamp": v.timestamp,
                "change_type": v.snapshot.change_type.value,
                "section": v.snapshot.section,
                "description": v.snapshot.description,
                "is_current": v.is_current,
            })
        return history

    def diff_versions(
        self, version_id_1: str, version_id_2: str
    ) -> tuple[bool, Optional[dict]]:
        """
        Compare two versions and return differences.

        Args:
            version_id_1: First version ID
            version_id_2: Second version ID

        Returns:
            (success, diff_dict)
        """
        v1 = self.get_version(version_id_1)
        v2 = self.get_version(version_id_2)

        if not v1 or not v2:
            return False, None

        # Simple diff: find changed sections
        diff = {
            "version_1": version_id_1,
            "version_2": version_id_2,
            "changes": [],
        }

        # Compare top-level keys
        keys1 = set(v1.report_content.keys())
        keys2 = set(v2.report_content.keys())

        for key in keys1 | keys2:
            val1 = v1.report_content.get(key, "")
            val2 = v2.report_content.get(key, "")

            if val1 != val2:
                diff["changes"].append({
                    "section": key,
                    "changed": True,
                })

        return True, diff

    def export_history(self) -> dict:
        """
        Export full version history as a serializable dict.

        Returns:
            Dictionary with all versions and metadata
        """
        return {
            "total_versions": len(self.versions),
            "current_version_id": self.get_current_version().version_id if self.get_current_version() else None,
            "versions": [v.to_dict() for v in self.versions],
        }

    def _prune_old_versions(self) -> None:
        """Remove oldest versions to stay under max_versions limit."""
        while len(self.versions) > self.max_versions:
            removed = self.versions.pop(0)
            logger.debug(f"Pruned old version: {removed.version_id}")
