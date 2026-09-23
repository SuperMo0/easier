"""Render a markdown CV to a PDF that reads like a CV rather than a web page.

Usage:
    python render_pdf.py applications/careem/cv.md applications/careem/cv.pdf
"""

import sys
from pathlib import Path

import markdown

STYLE = """
@page { size: A4; margin: 14mm 15mm; }
body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 9.5pt; line-height: 1.38; color: #1a1a1a; }
h1 { font-size: 19pt; text-align: center; margin: 0 0 2pt; letter-spacing: 0.4pt; color: #1f3352; }
h1 + p { text-align: center; margin: 0 0 10pt; font-size: 9pt; color: #444; }
h2 { font-size: 10.5pt; text-transform: uppercase; letter-spacing: 0.8pt; color: #1f3352;
     border-bottom: 1px solid #c3ccd8; padding-bottom: 2pt; margin: 13pt 0 6pt; }
h3 { font-size: 10pt; margin: 8pt 0 3pt; color: #12203a; }
ul { margin: 3pt 0 6pt; padding-left: 15pt; }
li { margin-bottom: 2.5pt; }
p { margin: 3pt 0; }
strong { color: #12203a; }
hr { display: none; }
table { border-collapse: collapse; margin: 4pt 0 8pt; }
th, td { text-align: left; padding: 2.5pt 12pt 2.5pt 0; border-bottom: 0.5pt solid #e1e6ee; vertical-align: top; }
th { color: #1f3352; }
/* Clickable but undecorated reads as plain text on paper and on screen, so the reader
   never tries the link. Colour marks them without the noise of underlines. */
a { color: #2a5db0; text-decoration: none; }
h1 + p a { border-bottom: 0.5pt solid #9db6dd; }
"""


def to_html(source: Path) -> str:
    # nl2br keeps the header, education lines and letter sign-off on their own lines.
    body = markdown.markdown(source.read_text(encoding="utf-8"), extensions=["tables", "nl2br"])
    return f"<html><head><meta charset='utf-8'><style>{STYLE}</style></head><body>{body}</body></html>"


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: render_pdf.py <input.md> <output.pdf>")

    source, target = Path(sys.argv[1]), Path(sys.argv[2])
    if not source.is_file():
        sys.exit(f"input not found: {source}")

    document = to_html(source)

    # Imported here so apply.py can reuse STYLE and to_html on machines without WeasyPrint.
    from weasyprint import HTML

    target.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=document).write_pdf(target)
    print(f"wrote {target} ({target.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
