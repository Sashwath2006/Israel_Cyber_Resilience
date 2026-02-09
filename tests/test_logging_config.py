"""
Unit Tests for Logging Configuration Module

Tests for logging setup, configuration, and functionality.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

from app.logging_config import setup_logging, get_logger


class TestLoggingConfiguration:
    """Test suite for logging configuration."""
    
    def test_setup_logging_basic(self):
        """Test that basic logging setup works."""
        # This test will set up logging and verify no exceptions occur
        try:
            setup_logging(log_level="INFO")
            # If we get here without exception, the basic setup worked
            assert True
        except Exception as e:
            pytest.fail(f"Basic logging setup failed: {e}")
    
    def test_setup_logging_with_file(self):
        """Test that logging setup with file output works."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as tmp:
            log_file = tmp.name
        
        try:
            setup_logging(log_level="INFO", log_file=log_file)
            # Verify the log file was created
            assert os.path.exists(log_file)
        finally:
            # Clean up
            if os.path.exists(log_file):
                os.unlink(log_file)
    
    def test_different_log_levels(self):
        """Test that different log levels can be configured."""
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in log_levels:
            try:
                setup_logging(log_level=level)
                # If we get here without exception, the level was accepted
                assert True
            except Exception as e:
                pytest.fail(f"Log level {level} failed to configure: {e}")
    
    def test_get_logger_returns_instance(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger()
        assert logger is not None
        
        # Test with a name
        named_logger = get_logger("test_component")
        assert named_logger is not None
    
    def test_logging_outputs_to_file(self):
        """Test that logging actually writes to file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as tmp:
            log_file = tmp.name
        
        try:
            setup_logging(log_level="INFO", log_file=log_file)
            
            # Get a logger and write a message
            logger = get_logger("test")
            logger.info("Test log message", test_param="value")
            
            # Wait a moment for async logging to complete
            import time
            time.sleep(0.1)
            
            # Verify the message was written to the file
            with open(log_file, 'r') as f:
                content = f.read()
                
            # The content should contain our test message
            assert "Test log message" in content
            assert "test_param" in content
            
        finally:
            # Clean up
            if os.path.exists(log_file):
                os.unlink(log_file)


class TestLoggingFunctionality:
    """Test suite for logging functionality."""
    
    def setup_method(self):
        """Set up logging for each test."""
        setup_logging(log_level="DEBUG")
    
    def test_logger_info_works(self):
        """Test that info logging works."""
        logger = get_logger("test_info")
        
        # This should not raise an exception
        logger.info("Test info message", param="value")
        assert True  # If we get here, no exception was raised
    
    def test_logger_error_works(self):
        """Test that error logging works."""
        logger = get_logger("test_error")
        
        # This should not raise an exception
        logger.error("Test error message", error_code=500)
        assert True  # If we get here, no exception was raised
    
    def test_logger_warning_works(self):
        """Test that warning logging works."""
        logger = get_logger("test_warning")
        
        # This should not raise an exception
        logger.warning("Test warning message", issue="potential_problem")
        assert True  # If we get here, no exception was raised
    
    def test_logger_debug_works(self):
        """Test that debug logging works."""
        logger = get_logger("test_debug")
        
        # This should not raise an exception
        logger.debug("Test debug message", variable="value")
        assert True  # If we get here, no exception was raised
    
    def test_structured_logging_with_context(self):
        """Test that structured logging preserves context."""
        logger = get_logger("test_structured")
        
        # Bind some context
        bound_logger = logger.bind(user_id=123, action="login")
        
        # Log with additional context
        bound_logger.info("User login attempt", success=True)
        assert True  # If we get here, no exception was raised


class TestLoggingEdgeCases:
    """Test suite for logging edge cases."""
    
    def test_logger_with_special_characters(self):
        """Test logging with special characters."""
        setup_logging(log_level="INFO")
        logger = get_logger("special_chars")
        
        # Test with various special characters
        special_messages = [
            "Message with newline\nhere",
            "Message with tab\there",
            "Message with 'quotes'",
            'Message with "double quotes"',
            "Message with émojis",
            "Message with \x00 null bytes",  # This might be problematic
        ]
        
        for msg in special_messages:
            try:
                logger.info(msg)
            except Exception as e:
                pytest.fail(f"Logging failed for special character message '{msg}': {e}")
    
    def test_logger_with_large_data(self):
        """Test logging with large data."""
        setup_logging(log_level="INFO")
        logger = get_logger("large_data")
        
        # Create a large string
        large_data = "x" * 10000  # 10KB string
        
        # This should not cause any issues
        logger.info("Large data test", data=large_data)
        assert True
    
    def test_concurrent_logging(self):
        """Test that logging works in concurrent scenarios."""
        import threading
        import time
        
        setup_logging(log_level="INFO")
        logger = get_logger("concurrent")
        
        results = []
        
        def log_from_thread(thread_id):
            for i in range(10):
                logger.info(f"Thread {thread_id}, message {i}", thread_id=thread_id)
            results.append(f"Thread {thread_id} completed")
        
        # Create multiple threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=log_from_thread, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Verify all threads completed
        assert len(results) == 3
        assert all("completed" in result for result in results)


if __name__ == "__main__":
    pytest.main([__file__])