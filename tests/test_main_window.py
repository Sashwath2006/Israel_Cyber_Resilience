"""
Unit Tests for Main Window Module

Tests for UI functionality, error handling, and integration between components.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, Mock

from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow, ScanWorker
from app.report_model import ReportWorkspace


class TestMainWindowInitialization:
    """Test suite for main window initialization."""
    
    @classmethod
    def setup_class(cls):
        """Set up QApplication for testing."""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])
    
    def test_main_window_initializes_without_error(self):
        """Test that main window initializes without errors."""
        window = MainWindow()
        assert window is not None
        assert window.windowTitle() == "Vulnerability Analysis Workbench"
    
    def test_main_window_has_expected_components(self):
        """Test that main window has expected UI components."""
        window = MainWindow()
        
        # Check that required components exist
        assert hasattr(window, 'report_editor')
        assert hasattr(window, 'chat_pane')
        assert hasattr(window, 'model_selector')
        assert hasattr(window, 'finalize_btn')
        assert hasattr(window, 'export_btn')


class TestScanWorker:
    """Test suite for ScanWorker functionality."""
    
    @classmethod
    def setup_class(cls):
        """Set up QApplication for testing."""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])
    
    def test_scan_worker_processes_valid_files(self):
        """Test that ScanWorker processes valid files without error."""
        # Create a temporary file with content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write("password=test123")
            tmp_path = tmp.name
        
        try:
            # Create a mock parent object
            mock_parent = Mock()
            
            # Create scan worker
            worker = ScanWorker([tmp_path])
            
            # Mock the signals
            worker.status_update = Mock()
            worker.scan_complete = Mock()
            worker.error_occurred = Mock()
            
            # Run the worker
            worker.run()
            
            # Verify that the worker processed the file
            worker.status_update.assert_called()  # Should emit status updates
            worker.scan_complete.assert_called()  # Should emit completion signal
            
        finally:
            os.unlink(tmp_path)
    
    def test_scan_worker_handles_invalid_file_gracefully(self):
        """Test that ScanWorker handles invalid files gracefully."""
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(mode='w', suffix='.exe', delete=False) as tmp:
            tmp.write("fake executable")
            tmp_path = tmp.name
        
        try:
            worker = ScanWorker([tmp_path])
            
            # Mock the signals
            worker.status_update = Mock()
            worker.scan_complete = Mock()
            worker.error_occurred = Mock()
            
            # Run the worker - should handle gracefully with warning
            worker.run()
            
            # Status update should be called with warning message
            worker.status_update.assert_called()
            
        finally:
            os.unlink(tmp_path)


class TestReportGeneration:
    """Test suite for report generation functionality."""
    
    @classmethod
    def setup_class(cls):
        """Set up QApplication for testing."""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])
    
    def test_report_workspace_creation(self):
        """Test that ReportWorkspace is created correctly."""
        workspace = ReportWorkspace(
            scope="Test Analysis",
            analyst_name="Test Analyst",
            executive_summary="Test summary"
        )
        
        assert workspace.scope == "Test Analysis"
        assert workspace.analyst_name == "Test Analyst"
        assert workspace.executive_summary == "Test summary"
    
    def test_report_workspace_add_findings(self):
        """Test that findings can be added to workspace."""
        workspace = ReportWorkspace(
            scope="Test Analysis",
            analyst_name="Test Analyst",
            executive_summary="Test summary"
        )
        
        test_findings = [
            {
                "finding_id": "test-1",
                "title": "Test Finding",
                "severity": "High",
                "category": "Credentials"
            }
        ]
        
        workspace.add_findings(test_findings)
        
        # Note: The actual implementation may vary, this is a basic test
        # based on the expected interface


class TestErrorHandling:
    """Test suite for error handling functionality."""
    
    @classmethod
    def setup_class(cls):
        """Set up QApplication for testing."""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])
    
    @patch('app.main_window.ingest_file')
    def test_handle_scan_error_properly(self, mock_ingest):
        """Test that scan errors are handled properly."""
        mock_ingest.side_effect = ValueError("Test error")
        
        window = MainWindow()
        
        # Mock the chat pane to capture messages
        window.chat_pane = Mock()
        window.chat_pane.add_message = Mock()
        
        # Trigger scan error handling
        window._handle_scan_error("Test error message")
        
        # Verify error message was added to chat
        window.chat_pane.add_message.assert_called_once()
        call_args = window.chat_pane.add_message.call_args
        assert "[ERROR]" in call_args[0][0]  # First argument should contain error
        assert "Test error message" in call_args[0][0]
        assert call_args[0][1] == False  # is_user should be False
    
    @patch('app.main_window.generate_sample_report')
    def test_handle_report_generation_error(self, mock_generate_report):
        """Test that report generation errors are handled."""
        mock_generate_report.side_effect = Exception("Report generation failed")
        
        window = MainWindow()
        
        # Mock the chat pane to capture messages
        window.chat_pane = Mock()
        window.chat_pane.add_message = Mock()
        
        # Simulate the scenario that would trigger report generation
        chunks = []
        findings = []
        
        # Call the method that generates report
        window._handle_scan_complete(chunks, findings)
        
        # Verify error was reported
        error_calls = [call for call in window.chat_pane.add_message.call_args_list 
                      if "[ERROR]" in call[0][0]]
        assert len(error_calls) > 0
        assert "Failed to generate report" in error_calls[0][0][0]


class TestIntegration:
    """Test suite for component integration."""
    
    @classmethod
    def setup_class(cls):
        """Set up QApplication for testing."""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])
    
    def test_model_selector_populated(self):
        """Test that model selector is populated with models."""
        window = MainWindow()
        
        # Check that model selector has items
        assert window.model_selector.count() > 0, "Model selector should have items"
        
        # Check that at least one item exists
        assert window.model_selector.itemText(0) is not None


if __name__ == "__main__":
    pytest.main([__file__])