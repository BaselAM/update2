from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextDocument


class PrintOperation:
    """Simple printing functionality for tables"""

    def __init__(self, parent_widget):
        """
        Initialize with just the parent widget

        Args:
            parent_widget: The QWidget that will be the parent of the print dialog
        """
        self.parent = parent_widget

    def print_table(self, table_widget):
        """
        Print a table widget

        Args:
            table_widget: The QTableWidget to print
        """
        try:
            # Create printer
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPrinter.A4)

            # Create preview dialog with the printer
            preview = QPrintPreviewDialog(printer, self.parent)
            preview.paintRequested.connect(
                lambda p: self._print_document(p, table_widget))
            preview.exec_()

        except Exception as e:
            print(f"Error in printing: {e}")

    def _print_document(self, printer, table):
        """Create and print the document"""
        # Create document and build HTML
        doc = QTextDocument()

        # Build simple HTML
        html = "<html><body>"
        html += "<h2 style='text-align:center;'>Products List</h2>"
        html += "<table border='1' cellpadding='4' width='100%'>"

        # Add headers
        html += "<tr bgcolor='#f0f0f0'>"
        for col in range(table.columnCount()):
            header = table.horizontalHeaderItem(col)
            header_text = header.text() if header else f"Column {col}"
            html += f"<th>{header_text}</th>"
        html += "</tr>"

        # Add data rows
        for row in range(table.rowCount()):
            html += "<tr>"
            for col in range(table.columnCount()):
                item = table.item(row, col)
                text = item.text() if item else ""
                html += f"<td>{text}</td>"
            html += "</tr>"

        html += "</table></body></html>"

        # Set content and print
        doc.setHtml(html)
        doc.print_(printer)