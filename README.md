# Quotation Station

A small, local quote manager and browser with a simple Tkinter GUI and a tiny helper library for persistence and fuzzy search.

**Features**
- Browse, search and filter quotes with a dark-themed Tkinter GUI.
- Fuzzy text search across quote text, author, and source.
- Add, edit and delete quotes (saved to `quotes.json`).

**Requirements**
- Python 3.8+
- Standard library only (Tkinter is required for the GUI; it is typically included with Python on most OSes).

This project does not require any pip-installable Python packages. A `requirements.txt` is included for clarity and contains guidance about the system Tkinter dependency and the minimum Python version.

**Installation**
1. Clone or copy the repository to a folder.
2. Ensure you have Python 3 installed and Tkinter available.

**Quick Start — GUI**
Run the graphical interface:

```bash
python3 quotes_gui.py
```

The GUI provides search, tag filtering, and forms for adding or editing quotes.

**Quick Start — CLI**
You can also use the small CLI in `quotes_helper.py` for quick fuzzy searches:

```bash
python3 quotes_helper.py "your search query" --min-score 0.35 --limit 10
# or search by tag
python3 quotes_helper.py --tag inspiration
```

**Files**
- `quotes_gui.py`: Tkinter GUI application. Launch this to run the desktop UI.
- `quotes_helper.py`: Data helpers and fuzzy search routines. Provides `load_quotes`, `add_quote`, `update_quote`, `delete_quote`, `fuzzy_search`, and a small CLI.
- `quotes.json`: Persistent store for quotes (JSON array). Created automatically when saving quotes.

**Data format (quotes.json)**
The file contains a JSON array of objects. Each quote object looks like:

```json
{
  "id": "<uuid>",
  "text": "Quote text...",
  "author": "Author Name",
  "source": "Source or book",
  "tags": ["tag1", "tag2"],
  "date": "YYYY-MM-DD",
  "notes": "Optional notes"
}
```

**Notes & Tips**
- Back up `quotes.json` before bulk-editing it by hand.
- The GUI uses a simple heuristic-based fuzzy search (no external dependencies).
- If Tkinter is not present on your platform, install the system package that provides it (e.g., `python3-tk` on Debian/Ubuntu).

