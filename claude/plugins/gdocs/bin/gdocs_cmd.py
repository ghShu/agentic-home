#!/usr/bin/env python3
"""Google Docs/Sheets/Slides CLI for the gdocs plugin.

Usage:
    gdocs_cmd read <url_or_id>                Read a Google Doc as plain text
    gdocs_cmd read-sheet <url_or_id> [sheet]  Read a Google Sheet (optionally specific sheet)
    gdocs_cmd read-slides <url_or_id>         Read Google Slides as text
    gdocs_cmd export <url_or_id> <format>     Export to format (txt/html/csv/pdf/docx/xlsx)
    gdocs_cmd info <url_or_id>                Show file metadata

Accepts full Google Docs URLs or just the document ID.
Authenticates via gcloud CLI (run: gcloud auth login --enable-gdrive-access).
"""

import os
import re
import sys
import urllib.error
import urllib.parse

_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
_LIB = os.path.join(_PLUGIN_DIR, "lib")
sys.path.insert(0, _LIB)
from google_auth import get_access_token, google_api_download, google_api_get  # noqa: E402


DOC_URL_PATTERNS = [
    r"docs\.google\.com/document/d/([a-zA-Z0-9_-]+)",
    r"docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)",
    r"docs\.google\.com/presentation/d/([a-zA-Z0-9_-]+)",
    r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",
]


def parse_doc_id(url_or_id):
    for pattern in DOC_URL_PATTERNS:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id.strip()


def detect_type(url_or_id):
    if "document" in url_or_id:
        return "doc"
    if "spreadsheet" in url_or_id:
        return "sheet"
    if "presentation" in url_or_id:
        return "slides"
    return None


def cmd_read(args):
    if not args:
        _die("Usage: gdocs_cmd read <url_or_id>")

    doc_id = parse_doc_id(args[0])
    doc_type = detect_type(args[0])
    token = get_access_token()

    if doc_type == "sheet":
        cmd_read_sheet([args[0]])
        return
    if doc_type == "slides":
        cmd_read_slides([args[0]])
        return

    data = google_api_get(f"https://docs.googleapis.com/v1/documents/{doc_id}", token)
    print(f"# {data.get('title', 'Untitled')}\n")
    _print_doc_body(data)


def cmd_read_sheet(args):
    if not args:
        _die("Usage: gdocs_cmd read-sheet <url_or_id> [sheet_name]")

    sheet_id = parse_doc_id(args[0])
    sheet_name = args[1] if len(args) > 1 else None
    token = get_access_token()

    meta = google_api_get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}",
        token,
        {"fields": "properties.title,sheets.properties"},
    )
    print(f"# {meta.get('properties', {}).get('title', 'Untitled')}\n")

    sheets = meta.get("sheets", [])
    if sheet_name:
        sheets = [s for s in sheets if s["properties"]["title"].lower() == sheet_name.lower()]
        if not sheets:
            _die(f"Sheet '{sheet_name}' not found")

    for sheet in sheets:
        title = sheet["properties"]["title"]
        print(f"\n## {title}\n")

        data = google_api_get(
            f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{urllib.parse.quote(title)}",
            token,
        )
        rows = data.get("values", [])
        if not rows:
            print("  (empty)")
            continue

        col_widths = []
        for row in rows[:100]:
            for i, cell in enumerate(row):
                while len(col_widths) <= i:
                    col_widths.append(0)
                col_widths[i] = max(col_widths[i], min(len(str(cell)), 40))

        for i, row in enumerate(rows):
            cells = [str(c).ljust(col_widths[j] if j < len(col_widths) else 10)[:40]
                     for j, c in enumerate(row)]
            print("  " + " | ".join(cells))
            if i == 0:
                print("  " + "-+-".join("-" * (col_widths[j] if j < len(col_widths) else 10)
                                        for j in range(len(row))))

        print(f"\n  ({len(rows)} rows)")


def cmd_read_slides(args):
    if not args:
        _die("Usage: gdocs_cmd read-slides <url_or_id>")

    slides_id = parse_doc_id(args[0])
    token = get_access_token()

    data = google_api_get(
        f"https://slides.googleapis.com/v1/presentations/{slides_id}",
        token,
    )
    print(f"# {data.get('title', 'Untitled')}\n")

    for i, slide in enumerate(data.get("slides", []), 1):
        print(f"\n## Slide {i}\n")
        for elem in slide.get("pageElements", []):
            shape = elem.get("shape", {})
            text = shape.get("text", {})
            for te in text.get("textElements", []):
                tr = te.get("textRun", {})
                content = tr.get("content", "").strip()
                if content:
                    print(f"  {content}")
            table = elem.get("table", {})
            for row in table.get("tableRows", []):
                cells = []
                for cell in row.get("tableCells", []):
                    cell_text = ""
                    for te in cell.get("text", {}).get("textElements", []):
                        cell_text += te.get("textRun", {}).get("content", "")
                    cells.append(cell_text.strip())
                if any(cells):
                    print("  " + " | ".join(cells))


def cmd_export(args):
    if len(args) < 2:
        _die("Usage: gdocs_cmd export <url_or_id> <format>\n"
             "  Formats: txt, html, csv, pdf, docx, xlsx, pptx")

    doc_id = parse_doc_id(args[0])
    fmt = args[1].lower()
    token = get_access_token()

    mime_map = {
        "txt": "text/plain",
        "html": "text/html",
        "csv": "text/csv",
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    mime = mime_map.get(fmt)
    if not mime:
        _die(f"Unknown format: {fmt}. Use: {', '.join(mime_map)}")

    url = f"https://www.googleapis.com/drive/v3/files/{doc_id}/export?mimeType={urllib.parse.quote(mime)}&supportsAllDrives=true"
    content = google_api_download(url, token)

    if fmt in ("txt", "html", "csv"):
        print(content.decode("utf-8", errors="replace"))
    else:
        outfile = f"{doc_id}.{fmt}"
        with open(outfile, "wb") as f:
            f.write(content)
        print(f"Exported to: {outfile} ({len(content)} bytes)")


def cmd_info(args):
    if not args:
        _die("Usage: gdocs_cmd info <url_or_id>")

    doc_id = parse_doc_id(args[0])
    token = get_access_token()

    data = google_api_get(
        f"https://www.googleapis.com/drive/v3/files/{doc_id}",
        token,
        {"fields": "id,name,mimeType,modifiedTime,lastModifyingUser,owners,size,webViewLink",
         "supportsAllDrives": "true"},
    )
    print(f"Name:     {data.get('name', '?')}")
    print(f"Type:     {data.get('mimeType', '?')}")
    print(f"Modified: {data.get('modifiedTime', '?')}")
    modifier = data.get("lastModifyingUser", {})
    print(f"By:       {modifier.get('displayName', '?')} ({modifier.get('emailAddress', '?')})")
    print(f"Link:     {data.get('webViewLink', '?')}")


def _print_doc_body(data):
    for elem in data.get("body", {}).get("content", []):
        para = elem.get("paragraph", {})
        style = para.get("paragraphStyle", {}).get("namedStyleType", "")

        parts = []
        for pe in para.get("elements", []):
            tr = pe.get("textRun", {})
            if tr.get("content"):
                parts.append(tr["content"])

        text = "".join(parts).rstrip()
        if not text:
            continue

        if "HEADING_1" in style:
            print(f"\n## {text}\n")
        elif "HEADING_2" in style:
            print(f"\n### {text}\n")
        elif "HEADING_3" in style:
            print(f"\n#### {text}\n")
        else:
            print(text)

    for elem in data.get("body", {}).get("content", []):
        table = elem.get("table")
        if not table:
            continue
        print()
        for row in table.get("tableRows", []):
            cells = []
            for cell in row.get("tableCells", []):
                cell_text = ""
                for content in cell.get("content", []):
                    for pe in content.get("paragraph", {}).get("elements", []):
                        cell_text += pe.get("textRun", {}).get("content", "")
                cells.append(cell_text.strip())
            print("  " + " | ".join(cells))
        print()


def _die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


COMMANDS = {
    "read": cmd_read,
    "read-sheet": cmd_read_sheet,
    "read-slides": cmd_read_slides,
    "export": cmd_export,
    "info": cmd_info,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__, file=sys.stderr)
        print(f"Commands: {', '.join(COMMANDS)}", file=sys.stderr)
        sys.exit(1)
    try:
        COMMANDS[sys.argv[1]](sys.argv[2:])
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        if "ACCESS_TOKEN_SCOPE_INSUFFICIENT" in body:
            _die("ERROR: Missing Drive scope. Run: gcloud auth login --enable-gdrive-access")
        _die(f"ERROR: HTTP {e.code}: {body}")
    except RuntimeError as e:
        _die(f"ERROR: {e}")
