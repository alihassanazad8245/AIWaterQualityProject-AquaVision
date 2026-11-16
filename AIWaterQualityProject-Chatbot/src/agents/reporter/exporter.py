from pathlib import Path
import re

from docx import Document


class DocxExporter:
    """Convert the project's Markdown reports to Word documents."""

    @staticmethod
    def table_cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    def export(self, markdown_content: str, output_path: str) -> str:
        doc = Document()
        lines = markdown_content.splitlines()
        index = 0
        while index < len(lines):
            line = lines[index]
            line_clean = line.strip()
            if line_clean.startswith("|") and index + 1 < len(lines):
                separator = lines[index + 1].strip()
                if separator.startswith("|") and re.fullmatch(r"[\s|:-]+", separator):
                    headers = self.table_cells(line_clean)
                    table = doc.add_table(rows=1, cols=len(headers))
                    table.style = "Light Shading Accent 1"
                    for cell, value in zip(table.rows[0].cells, headers):
                        cell.text = value.replace("**", "").replace("*", "")
                    index += 2
                    while index < len(lines) and lines[index].strip().startswith("|"):
                        values = self.table_cells(lines[index])
                        cells = table.add_row().cells
                        for cell, value in zip(cells, values):
                            cell.text = value.replace("**", "").replace("*", "")
                        index += 1
                    continue
            if line_clean.startswith("#"):
                heading_level = min(len(line_clean) - len(line_clean.lstrip("#")), 3)
                heading = line_clean.lstrip("#").strip()
                doc.add_heading(heading, level=heading_level)
            elif line_clean and not re.fullmatch(r"[-*_ ]+", line_clean):
                doc.add_paragraph(line_clean.replace("**", "").replace("*", ""))
            index += 1

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(out))
        return str(out)


_docx_exporter = DocxExporter()


def _table_cells(line: str) -> list[str]:
    return _docx_exporter.table_cells(line)


def export_to_docx(markdown_content: str, output_path: str) -> str:
    return _docx_exporter.export(markdown_content, output_path)