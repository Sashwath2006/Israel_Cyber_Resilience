def _handle_scan_button(self):
    """Handle scan button click from navigation bar."""
    paths, _ = QFileDialog.getOpenFileNames(self, "Select Files to Analyze", "", "All Files (*.*)")
    if paths:
        self._handle_file_upload(paths)

def _show_export_menu(self):
    """Show export menu from navigation bar."""
    menu = QMenu(self)
    menu.addAction("Export as Markdown", self._export_markdown)
    menu.addAction("Export as PDF", self._export_pdf)
    # Show menu near export button
    cursor = QApplication.instance().exec()
