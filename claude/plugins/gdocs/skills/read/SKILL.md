---
name: gdocs:read
description: Read Google Docs, Sheets, and Slides content. Use when the user shares a Google Docs/Sheets/Slides URL or asks to read/fetch content from Google Workspace documents.
argument-hint: "<google-docs-url>"
allowed-tools: ["Bash", "Read"]
user-invocable: true
---

# gdocs:read

Read content from Google Workspace documents directly from the CLI.
Authenticates via gcloud CLI — no API keys or service accounts needed.

## Arguments

The user provides:
- A Google Docs/Sheets/Slides URL (e.g., `https://docs.google.com/document/d/.../edit`)
- Or a document ID directly
- Optionally a specific sheet name for spreadsheets

## CLI Reference

All commands go through a single binary, `gdocs_cmd`, installed in `~/bin/`
by `install.sh`:

| Command | Description |
|---------|-------------|
| `gdocs_cmd read <url_or_id>` | Read a Doc/Sheet/Slides as plain text (auto-detects type) |
| `gdocs_cmd read-sheet <url_or_id> [sheet]` | Read a spreadsheet, optionally a specific sheet |
| `gdocs_cmd read-slides <url_or_id>` | Read slides as text |
| `gdocs_cmd export <url_or_id> <fmt>` | Export to format: txt, html, csv, pdf, docx, xlsx, pptx |
| `gdocs_cmd info <url_or_id>` | Show file metadata (name, type, modified, owner) |

### Examples

```bash
# Read a Google Doc
gdocs_cmd read "https://docs.google.com/document/d/1abc.../edit"

# Read a specific sheet tab
gdocs_cmd read-sheet "https://docs.google.com/spreadsheets/d/1abc.../edit" "Sheet2"

# Export a doc as HTML
gdocs_cmd export "https://docs.google.com/document/d/1abc.../edit" html

# Get file info
gdocs_cmd info "https://docs.google.com/document/d/1abc.../edit"
```

## Workflow

### Step 1: Fetch document content

The `read` command auto-detects the document type from the URL and uses the appropriate API (Docs, Sheets, or Slides).

### Step 2: Present the content

- For Docs: rendered as markdown-like plain text with headings
- For Sheets: rendered as aligned tables with headers
- For Slides: text extracted per slide

If the user asks about specific sections, use the output to answer their questions.

## Prerequisites

- gcloud CLI installed and authenticated with Drive scope:
  ```bash
  gcloud auth login --enable-gdrive-access
  ```
- Access to the Google Workspace document (must be shared with your Google account)
